"use client";

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PersonalInfo, FormStepProps } from '@/types';
import { personalInfoSchema, PersonalInfoFormData } from '@/lib/validationSchemas';

const US_STATES = [
  { value: 'AL', label: 'Alabama' },
  { value: 'AK', label: 'Alaska' },
  { value: 'AZ', label: 'Arizona' },
  { value: 'AR', label: 'Arkansas' },
  { value: 'CA', label: 'California' },
  { value: 'CO', label: 'Colorado' },
  { value: 'CT', label: 'Connecticut' },
  { value: 'DE', label: 'Delaware' },
  { value: 'FL', label: 'Florida' },
  { value: 'GA', label: 'Georgia' },
  { value: 'HI', label: 'Hawaii' },
  { value: 'ID', label: 'Idaho' },
  { value: 'IL', label: 'Illinois' },
  { value: 'IN', label: 'Indiana' },
  { value: 'IA', label: 'Iowa' },
  { value: 'KS', label: 'Kansas' },
  { value: 'KY', label: 'Kentucky' },
  { value: 'LA', label: 'Louisiana' },
  { value: 'ME', label: 'Maine' },
  { value: 'MD', label: 'Maryland' },
  { value: 'MA', label: 'Massachusetts' },
  { value: 'MI', label: 'Michigan' },
  { value: 'MN', label: 'Minnesota' },
  { value: 'MS', label: 'Mississippi' },
  { value: 'MO', label: 'Missouri' },
  { value: 'MT', label: 'Montana' },
  { value: 'NE', label: 'Nebraska' },
  { value: 'NV', label: 'Nevada' },
  { value: 'NH', label: 'New Hampshire' },
  { value: 'NJ', label: 'New Jersey' },
  { value: 'NM', label: 'New Mexico' },
  { value: 'NY', label: 'New York' },
  { value: 'NC', label: 'North Carolina' },
  { value: 'ND', label: 'North Dakota' },
  { value: 'OH', label: 'Ohio' },
  { value: 'OK', label: 'Oklahoma' },
  { value: 'OR', label: 'Oregon' },
  { value: 'PA', label: 'Pennsylvania' },
  { value: 'RI', label: 'Rhode Island' },
  { value: 'SC', label: 'South Carolina' },
  { value: 'SD', label: 'South Dakota' },
  { value: 'TN', label: 'Tennessee' },
  { value: 'TX', label: 'Texas' },
  { value: 'UT', label: 'Utah' },
  { value: 'VT', label: 'Vermont' },
  { value: 'VA', label: 'Virginia' },
  { value: 'WA', label: 'Washington' },
  { value: 'WV', label: 'West Virginia' },
  { value: 'WI', label: 'Wisconsin' },
  { value: 'WY', label: 'Wyoming' },
];

const MARITAL_STATUS_OPTIONS = [
  { value: 'single', label: 'Single' },
  { value: 'married', label: 'Married' },
  { value: 'divorced', label: 'Divorced' },
  { value: 'widowed', label: 'Widowed' },
];

export default function PersonalInfoForm({ data, onNext, onPrev }: FormStepProps<PersonalInfo>) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid },
  } = useForm<PersonalInfoFormData>({
    resolver: zodResolver(personalInfoSchema),
    defaultValues: data,
    mode: 'onChange',
  });

  const watchedValues = watch();

  const onSubmit = (formData: PersonalInfoFormData) => {
    onNext(formData);
  };

  return (
    <div id="personal-info-form" className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Personal Information</CardTitle>
          <p className="text-sm text-muted-foreground">
            Let's start with some basic information about you. This helps us create a personalized financial plan.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="age-input"
                label="Current Age"
                type="number"
                {...register('age', { valueAsNumber: true })}
                error={errors.age?.message}
                helperText="Your current age in years"
                required
              />
              
              <Input
                id="retirement-age-input"
                label="Planned Retirement Age"
                type="number"
                {...register('retirementAge', { valueAsNumber: true })}
                error={errors.retirementAge?.message}
                helperText="When do you plan to retire?"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                onValueChange={(value) => setValue('maritalStatus', value as PersonalInfo['maritalStatus'])}
                defaultValue={data.maritalStatus}
              >
                <SelectTrigger 
                  id="marital-status-select"
                  label="Marital Status" 
                  required
                  error={errors.maritalStatus?.message}
                >
                  <SelectValue placeholder="Select marital status" />
                </SelectTrigger>
                <SelectContent>
                  {MARITAL_STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Input
                id="dependents-input"
                label="Number of Dependents"
                type="number"
                {...register('dependents', { valueAsNumber: true })}
                error={errors.dependents?.message}
                helperText="Children or other dependents you support"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                onValueChange={(value) => setValue('state', value)}
                defaultValue={data.state}
              >
                <SelectTrigger 
                  id="state-select"
                  label="State" 
                  required
                  error={errors.state?.message}
                >
                  <SelectValue placeholder="Select your state" />
                </SelectTrigger>
                <SelectContent>
                  {US_STATES.map((state) => (
                    <SelectItem key={state.value} value={state.value}>
                      {state.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Input
                id="zip-code-input"
                label="ZIP Code"
                {...register('zipCode')}
                error={errors.zipCode?.message}
                helperText="Your primary residence ZIP code"
                required
              />
            </div>

            <div className="flex justify-between pt-4">
              <Button
                id="personal-info-prev-button"
                type="button"
                variant="outline"
                onClick={onPrev}
                disabled
              >
                Previous
              </Button>
              <Button
                id="personal-info-next-button"
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