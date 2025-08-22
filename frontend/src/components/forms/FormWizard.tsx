"use client";

import React from 'react';
import { useFinancialPlanningStore } from '@/store';
import { Progress } from '@/components/ui/progress';
import { Card } from '@/components/ui/card';
import { FormStep, StepConfig } from '@/types';
import PersonalInfoForm from './PersonalInfoForm';
import FinancialSnapshotForm from './FinancialSnapshotForm';
import AccountBucketsForm from './AccountBucketsForm';
import RiskPreferenceForm from './RiskPreferenceForm';
import RetirementGoalsForm from './RetirementGoalsForm';
import FormReview from './FormReview';

const FORM_STEPS: StepConfig[] = [
  {
    id: 'personal-info',
    title: 'Personal Information',
    description: 'Basic information about you',
    estimatedTime: 2,
  },
  {
    id: 'financial-snapshot',
    title: 'Financial Snapshot',
    description: 'Your current financial situation',
    estimatedTime: 3,
  },
  {
    id: 'account-buckets',
    title: 'Account Buckets',
    description: 'Your investment accounts',
    estimatedTime: 3,
  },
  {
    id: 'risk-preference',
    title: 'Risk Preference',
    description: 'Your investment comfort level',
    estimatedTime: 2,
  },
  {
    id: 'retirement-goals',
    title: 'Retirement Goals',
    description: 'Your retirement aspirations',
    estimatedTime: 3,
  },
  {
    id: 'review',
    title: 'Review',
    description: 'Review and submit',
    estimatedTime: 2,
  },
];

export default function FormWizard() {
  const {
    formData,
    currentStep,
    completedSteps,
    getFormProgress,
    setPersonalInfo,
    setFinancialSnapshot,
    setAccountBuckets,
    setRiskPreference,
    setRetirementGoals,
    nextStep,
    prevStep,
    goToStep,
  } = useFinancialPlanningStore();

  const currentStepIndex = FORM_STEPS.findIndex(step => step.id === currentStep);
  const currentStepConfig = FORM_STEPS[currentStepIndex];
  const progress = getFormProgress();

  const handleNext = (data: any) => {
    // Save data based on current step
    switch (currentStep) {
      case 'personal-info':
        setPersonalInfo(data);
        break;
      case 'financial-snapshot':
        setFinancialSnapshot(data);
        break;
      case 'account-buckets':
        setAccountBuckets(data);
        break;
      case 'risk-preference':
        setRiskPreference(data);
        break;
      case 'retirement-goals':
        setRetirementGoals(data);
        break;
      case 'review':
        // Trigger submission by dispatching a custom event
        const submitEvent = new CustomEvent('financialPlanSubmit', { 
          detail: formData 
        });
        window.dispatchEvent(submitEvent);
        return;
    }
    
    nextStep();
  };

  const handlePrev = () => {
    prevStep();
  };

  const handleEdit = (stepId: string) => {
    goToStep(stepId as FormStep);
  };

  const renderStepComponent = () => {
    const commonProps = {
      onNext: handleNext,
      onPrev: handlePrev,
    };

    switch (currentStep) {
      case 'personal-info':
        return (
          <PersonalInfoForm
            data={formData.personalInfo!}
            {...commonProps}
          />
        );
      case 'financial-snapshot':
        return (
          <FinancialSnapshotForm
            data={formData.financialSnapshot!}
            {...commonProps}
          />
        );
      case 'account-buckets':
        return (
          <AccountBucketsForm
            data={formData.accountBuckets!}
            {...commonProps}
          />
        );
      case 'risk-preference':
        return (
          <RiskPreferenceForm
            data={formData.riskPreference!}
            {...commonProps}
          />
        );
      case 'retirement-goals':
        return (
          <RetirementGoalsForm
            data={formData.retirementGoals!}
            {...commonProps}
          />
        );
      case 'review':
        return (
          <FormReview
            data={formData}
            onEdit={handleEdit}
            {...commonProps}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div id="form-wizard" className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Progress Header */}
        <div id="form-wizard-header" className="mb-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-6">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                AI Financial Planning
              </h1>
              <p className="text-lg text-muted-foreground">
                Complete your financial profile in about 10 minutes
              </p>
            </div>

            {/* Step Progress */}
            <Card className="p-6 mb-6">
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Step {currentStepIndex + 1} of {FORM_STEPS.length}: {currentStepConfig.title}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    ~{currentStepConfig.estimatedTime} min
                  </span>
                </div>
                <Progress 
                  value={progress} 
                  showLabel 
                  steps={FORM_STEPS.map((step, index) => ({
                    label: step.title,
                    completed: completedSteps.includes(step.id) || index < currentStepIndex,
                  }))}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                {currentStepConfig.description}
              </p>
            </Card>

            {/* Step Navigation Pills */}
            <div id="step-navigation" className="flex flex-wrap justify-center gap-2 mb-8">
              {FORM_STEPS.map((step, index) => {
                const isCompleted = completedSteps.includes(step.id);
                const isCurrent = step.id === currentStep;
                const isAccessible = isCompleted || isCurrent || index === 0;
                
                return (
                  <button
                    key={step.id}
                    id={`step-nav-${step.id}`}
                    onClick={() => isAccessible && goToStep(step.id)}
                    disabled={!isAccessible}
                    className={`
                      px-3 py-1 rounded-full text-sm font-medium transition-colors
                      ${isCurrent 
                        ? 'bg-primary text-primary-foreground' 
                        : isCompleted
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-800'
                        : isAccessible
                        ? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                        : 'bg-gray-50 text-gray-400 dark:bg-gray-900 dark:text-gray-600 cursor-not-allowed'
                      }
                    `}
                    aria-current={isCurrent ? 'step' : undefined}
                    aria-label={`Step ${index + 1}: ${step.title}${isCompleted ? ' (completed)' : ''}`}
                  >
                    {step.title}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Form Content */}
        <div id="form-content" className="mb-8">
          {renderStepComponent()}
        </div>

        {/* Footer */}
        <div id="form-wizard-footer" className="text-center">
          <p className="text-sm text-muted-foreground">
            Your data is encrypted and secure. We never share your personal information.
          </p>
        </div>
      </div>
    </div>
  );
}