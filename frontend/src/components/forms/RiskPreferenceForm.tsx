"use client";

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RiskPreference, FormStepProps } from '@/types';
import { riskPreferenceSchema, RiskPreferenceFormData } from '@/lib/validationSchemas';

const RISK_TOLERANCE_OPTIONS = [
  {
    value: 'conservative',
    label: 'Conservative',
    description: 'Prefer stability over growth, minimal risk'
  },
  {
    value: 'moderate',
    label: 'Moderate',
    description: 'Balanced approach to risk and return'
  },
  {
    value: 'aggressive',
    label: 'Aggressive',
    description: 'Willing to take significant risk for higher returns'
  },
  {
    value: 'very_aggressive',
    label: 'Very Aggressive',
    description: 'Comfortable with high volatility for maximum growth'
  }
];

const VOLATILITY_COMFORT_LEVELS = [
  { value: 1, label: '1 - Very Uncomfortable', description: 'Any loss makes me very anxious' },
  { value: 2, label: '2 - Uncomfortable', description: 'Small losses concern me' },
  { value: 3, label: '3 - Neutral', description: 'I can handle moderate fluctuations' },
  { value: 4, label: '4 - Comfortable', description: 'I can handle significant swings' },
  { value: 5, label: '5 - Very Comfortable', description: 'Market volatility doesn\'t bother me' }
];

const MARKET_REACTION_OPTIONS = [
  {
    value: 'sell',
    label: 'Sell investments',
    description: 'I would likely sell to avoid further losses'
  },
  {
    value: 'hold',
    label: 'Hold steady',
    description: 'I would maintain my current investments'
  },
  {
    value: 'buy_more',
    label: 'Buy more',
    description: 'I would see it as a buying opportunity'
  }
];

const EXPERIENCE_LEVELS = [
  { value: 'beginner', label: 'Beginner', description: 'Little to no investment experience' },
  { value: 'intermediate', label: 'Intermediate', description: 'Some experience with basic investments' },
  { value: 'advanced', label: 'Advanced', description: 'Experienced with various investment types' },
  { value: 'expert', label: 'Expert', description: 'Extensive experience and knowledge' }
];

export default function RiskPreferenceForm({ 
  data, 
  onNext, 
  onPrev 
}: FormStepProps<RiskPreference>) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid },
  } = useForm<RiskPreferenceFormData>({
    resolver: zodResolver(riskPreferenceSchema),
    defaultValues: data,
    mode: 'onChange',
  });

  const watchedValues = watch();

  const onSubmit = (formData: RiskPreferenceFormData) => {
    onNext(formData);
  };

  const getRiskDescription = () => {
    const { riskTolerance, volatilityComfort, investmentExperience } = watchedValues;
    
    if (!riskTolerance) return '';
    
    const riskLevel = RISK_TOLERANCE_OPTIONS.find(r => r.value === riskTolerance);
    const volatilityLevel = VOLATILITY_COMFORT_LEVELS.find(v => v.value === volatilityComfort);
    const experienceLevel = EXPERIENCE_LEVELS.find(e => e.value === investmentExperience);
    
    return `Based on your ${riskLevel?.label.toLowerCase()} risk tolerance, ${volatilityLevel?.label.toLowerCase()} with volatility, and ${experienceLevel?.label.toLowerCase()} experience level, we'll recommend an appropriate portfolio allocation.`;
  };

  return (
    <div id="risk-preference-form" className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Risk Preference</CardTitle>
          <p className="text-sm text-muted-foreground">
            Understanding your comfort level with investment risk helps us create the right portfolio for you.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-4">
              <Select
                onValueChange={(value) => setValue('riskTolerance', value as RiskPreference['riskTolerance'])}
                defaultValue={data.riskTolerance}
              >
                <SelectTrigger 
                  id="risk-tolerance-select"
                  label="Risk Tolerance" 
                  required
                  error={errors.riskTolerance?.message}
                >
                  <SelectValue placeholder="Select your risk tolerance" />
                </SelectTrigger>
                <SelectContent>
                  {RISK_TOLERANCE_OPTIONS.map((option) => (
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="time-horizon-input"
                label="Investment Time Horizon (Years)"
                type="number"
                {...register('timeHorizon', { valueAsNumber: true })}
                error={errors.timeHorizon?.message}
                helperText="How many years until you need this money?"
                required
              />

              <Select
                onValueChange={(value) => setValue('volatilityComfort', parseInt(value) as RiskPreference['volatilityComfort'])}
                defaultValue={data.volatilityComfort?.toString()}
              >
                <SelectTrigger 
                  id="volatility-comfort-select"
                  label="Comfort with Volatility" 
                  required
                  error={errors.volatilityComfort?.message}
                >
                  <SelectValue placeholder="Rate your comfort level" />
                </SelectTrigger>
                <SelectContent>
                  {VOLATILITY_COMFORT_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value.toString()}>
                      <div>
                        <div className="font-medium">{level.label}</div>
                        <div className="text-sm text-muted-foreground">{level.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-4">
              <Select
                onValueChange={(value) => setValue('marketDownturnReaction', value as RiskPreference['marketDownturnReaction'])}
                defaultValue={data.marketDownturnReaction}
              >
                <SelectTrigger 
                  id="market-reaction-select"
                  label="Market Downturn Reaction" 
                  required
                  error={errors.marketDownturnReaction?.message}
                >
                  <SelectValue placeholder="If the market dropped 20%, I would..." />
                </SelectTrigger>
                <SelectContent>
                  {MARKET_REACTION_OPTIONS.map((option) => (
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

            <div className="space-y-4">
              <Select
                onValueChange={(value) => setValue('investmentExperience', value as RiskPreference['investmentExperience'])}
                defaultValue={data.investmentExperience}
              >
                <SelectTrigger 
                  id="investment-experience-select"
                  label="Investment Experience" 
                  required
                  error={errors.investmentExperience?.message}
                >
                  <SelectValue placeholder="Select your experience level" />
                </SelectTrigger>
                <SelectContent>
                  {EXPERIENCE_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      <div>
                        <div className="font-medium">{level.label}</div>
                        <div className="text-sm text-muted-foreground">{level.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Risk Profile Summary */}
            {getRiskDescription() && (
              <div id="risk-profile-summary" className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">Your Risk Profile</h3>
                <p className="text-sm text-blue-800 dark:text-blue-200">{getRiskDescription()}</p>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button
                id="risk-preference-prev-button"
                type="button"
                variant="outline"
                onClick={onPrev}
              >
                Previous
              </Button>
              <Button
                id="risk-preference-next-button"
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