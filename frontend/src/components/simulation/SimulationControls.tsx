import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { InfoIcon, PlayIcon, SettingsIcon, TrendingUpIcon } from 'lucide-react';
import { Switch } from '@/components/ui/switch';

export interface SimulationParameters {
  // Basic Parameters
  timeHorizon: number;
  initialInvestment: number;
  monthlyContribution: number;
  
  // Market Parameters
  expectedReturn: number;
  volatility: number;
  riskFreeRate: number;
  
  // Advanced Parameters
  numSimulations: number;
  jumpIntensity: number;
  jumpSizeMean: number;
  jumpSizeStd: number;
  
  // Regime Parameters
  enableRegimeSwitching: boolean;
  regimeDetection: boolean;
  
  // Goal Parameters
  targetAmount?: number;
  successThreshold: number;
}

interface SimulationControlsProps {
  parameters: SimulationParameters;
  onParametersChange: (parameters: SimulationParameters) => void;
  onRunSimulation: () => void;
  isRunning: boolean;
  className?: string;
}

const SimulationControls: React.FC<SimulationControlsProps> = ({
  parameters,
  onParametersChange,
  onRunSimulation,
  isRunning,
  className = ""
}) => {
  const updateParameter = (key: keyof SimulationParameters, value: any) => {
    onParametersChange({ ...parameters, [key]: value });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <Card className={`w-full ${className}`} id="simulation-controls-card">
      <CardHeader id="simulation-controls-header">
        <div className="flex items-center justify-between" id="controls-header-content">
          <div id="controls-title-section">
            <CardTitle className="flex items-center gap-2" id="controls-title">
              <SettingsIcon className="h-5 w-5" />
              Simulation Parameters
            </CardTitle>
            <CardDescription id="controls-description">
              Configure your Monte Carlo simulation parameters and scenarios
            </CardDescription>
          </div>
          <Button 
            onClick={onRunSimulation} 
            disabled={isRunning}
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            id="run-simulation-button"
          >
            {isRunning ? (
              <div className="flex items-center gap-2" id="loading-content">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" id="loading-spinner" />
                Running...
              </div>
            ) : (
              <div className="flex items-center gap-2" id="run-content">
                <PlayIcon className="h-4 w-4" />
                Run Simulation
              </div>
            )}
          </Button>
        </div>
      </CardHeader>
      
      <CardContent id="simulation-controls-content">
        <Tabs defaultValue="basic" className="w-full" id="simulation-tabs">
          <TabsList className="grid w-full grid-cols-3" id="tabs-list">
            <TabsTrigger value="basic" id="basic-tab">Basic</TabsTrigger>
            <TabsTrigger value="market" id="market-tab">Market</TabsTrigger>
            <TabsTrigger value="advanced" id="advanced-tab">Advanced</TabsTrigger>
          </TabsList>
          
          <TabsContent value="basic" className="space-y-6" id="basic-tab-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6" id="basic-parameters-grid">
              {/* Time Horizon */}
              <div className="space-y-2" id="time-horizon-section">
                <Label htmlFor="time-horizon" className="text-sm font-medium">
                  Time Horizon (Years)
                </Label>
                <div className="space-y-2" id="time-horizon-controls">
                  <Slider
                    id="time-horizon"
                    min={1}
                    max={50}
                    step={1}
                    value={[parameters.timeHorizon]}
                    onValueChange={([value]) => updateParameter('timeHorizon', value)}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground" id="time-horizon-labels">
                    <span>1 year</span>
                    <Badge variant="secondary" id="time-horizon-value">{parameters.timeHorizon} years</Badge>
                    <span>50 years</span>
                  </div>
                </div>
              </div>

              {/* Initial Investment */}
              <div className="space-y-2" id="initial-investment-section">
                <Label htmlFor="initial-investment" className="text-sm font-medium">
                  Initial Investment
                </Label>
                <div className="relative" id="initial-investment-input-container">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">$</span>
                  <Input
                    id="initial-investment"
                    type="number"
                    value={parameters.initialInvestment}
                    onChange={(e) => updateParameter('initialInvestment', parseInt(e.target.value) || 0)}
                    className="pl-7"
                    placeholder="100000"
                  />
                </div>
                <div className="text-xs text-muted-foreground" id="initial-investment-display">
                  {formatCurrency(parameters.initialInvestment)}
                </div>
              </div>

              {/* Monthly Contribution */}
              <div className="space-y-2" id="monthly-contribution-section">
                <Label htmlFor="monthly-contribution" className="text-sm font-medium">
                  Monthly Contribution
                </Label>
                <div className="relative" id="monthly-contribution-input-container">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">$</span>
                  <Input
                    id="monthly-contribution"
                    type="number"
                    value={parameters.monthlyContribution}
                    onChange={(e) => updateParameter('monthlyContribution', parseInt(e.target.value) || 0)}
                    className="pl-7"
                    placeholder="1000"
                  />
                </div>
                <div className="text-xs text-muted-foreground" id="monthly-contribution-display">
                  {formatCurrency(parameters.monthlyContribution)} per month
                </div>
              </div>

              {/* Target Amount */}
              <div className="space-y-2" id="target-amount-section">
                <Label htmlFor="target-amount" className="text-sm font-medium">
                  Target Amount (Optional)
                </Label>
                <div className="relative" id="target-amount-input-container">
                  <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground">$</span>
                  <Input
                    id="target-amount"
                    type="number"
                    value={parameters.targetAmount || ''}
                    onChange={(e) => updateParameter('targetAmount', parseInt(e.target.value) || undefined)}
                    className="pl-7"
                    placeholder="1000000"
                  />
                </div>
                <div className="text-xs text-muted-foreground" id="target-amount-display">
                  {parameters.targetAmount ? formatCurrency(parameters.targetAmount) : 'No target set'}
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="market" className="space-y-6" id="market-tab-content">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6" id="market-parameters-grid">
              {/* Expected Return */}
              <div className="space-y-2" id="expected-return-section">
                <Label htmlFor="expected-return" className="text-sm font-medium">
                  Expected Annual Return
                </Label>
                <div className="space-y-2" id="expected-return-controls">
                  <Slider
                    id="expected-return"
                    min={0}
                    max={0.20}
                    step={0.001}
                    value={[parameters.expectedReturn]}
                    onValueChange={([value]) => updateParameter('expectedReturn', value)}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground" id="expected-return-labels">
                    <span>0%</span>
                    <Badge variant="secondary" id="expected-return-value">
                      {formatPercent(parameters.expectedReturn)}
                    </Badge>
                    <span>20%</span>
                  </div>
                </div>
              </div>

              {/* Volatility */}
              <div className="space-y-2" id="volatility-section">
                <Label htmlFor="volatility" className="text-sm font-medium">
                  Volatility (Standard Deviation)
                </Label>
                <div className="space-y-2" id="volatility-controls">
                  <Slider
                    id="volatility"
                    min={0.05}
                    max={0.40}
                    step={0.001}
                    value={[parameters.volatility]}
                    onValueChange={([value]) => updateParameter('volatility', value)}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground" id="volatility-labels">
                    <span>5%</span>
                    <Badge variant="secondary" id="volatility-value">
                      {formatPercent(parameters.volatility)}
                    </Badge>
                    <span>40%</span>
                  </div>
                </div>
              </div>

              {/* Risk-Free Rate */}
              <div className="space-y-2" id="risk-free-rate-section">
                <Label htmlFor="risk-free-rate" className="text-sm font-medium">
                  Risk-Free Rate
                </Label>
                <div className="space-y-2" id="risk-free-rate-controls">
                  <Slider
                    id="risk-free-rate"
                    min={0}
                    max={0.08}
                    step={0.001}
                    value={[parameters.riskFreeRate]}
                    onValueChange={([value]) => updateParameter('riskFreeRate', value)}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground" id="risk-free-rate-labels">
                    <span>0%</span>
                    <Badge variant="secondary" id="risk-free-rate-value">
                      {formatPercent(parameters.riskFreeRate)}
                    </Badge>
                    <span>8%</span>
                  </div>
                </div>
              </div>

              {/* Success Threshold */}
              <div className="space-y-2" id="success-threshold-section">
                <Label htmlFor="success-threshold" className="text-sm font-medium">
                  Success Threshold
                </Label>
                <div className="space-y-2" id="success-threshold-controls">
                  <Slider
                    id="success-threshold"
                    min={0.5}
                    max={1.0}
                    step={0.01}
                    value={[parameters.successThreshold]}
                    onValueChange={([value]) => updateParameter('successThreshold', value)}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-muted-foreground" id="success-threshold-labels">
                    <span>50%</span>
                    <Badge variant="secondary" id="success-threshold-value">
                      {formatPercent(parameters.successThreshold)}
                    </Badge>
                    <span>100%</span>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="advanced" className="space-y-6" id="advanced-tab-content">
            <div className="grid grid-cols-1 gap-6" id="advanced-parameters-grid">
              {/* Number of Simulations */}
              <div className="space-y-2" id="num-simulations-section">
                <Label htmlFor="num-simulations" className="text-sm font-medium">
                  Number of Simulations
                </Label>
                <Select 
                  value={parameters.numSimulations.toString()} 
                  onValueChange={(value) => updateParameter('numSimulations', parseInt(value))}
                >
                  <SelectTrigger id="num-simulations">
                    <SelectValue placeholder="Select number of simulations" />
                  </SelectTrigger>
                  <SelectContent id="num-simulations-options">
                    <SelectItem value="1000">1,000 (Fast)</SelectItem>
                    <SelectItem value="10000">10,000 (Standard)</SelectItem>
                    <SelectItem value="50000">50,000 (Detailed)</SelectItem>
                    <SelectItem value="100000">100,000 (Comprehensive)</SelectItem>
                  </SelectContent>
                </Select>
                <div className="text-xs text-muted-foreground" id="num-simulations-note">
                  More simulations provide higher accuracy but take longer to compute
                </div>
              </div>

              <Separator id="advanced-separator-1" />

              {/* Regime Switching */}
              <div className="space-y-4" id="regime-switching-section">
                <div className="flex items-center justify-between" id="regime-switching-header">
                  <div id="regime-switching-info">
                    <Label className="text-sm font-medium">Market Regime Switching</Label>
                    <div className="text-xs text-muted-foreground">
                      Enable market regime detection for bull/bear cycles
                    </div>
                  </div>
                  <Switch
                    id="regime-switching-toggle"
                    checked={parameters.enableRegimeSwitching}
                    onCheckedChange={(checked) => updateParameter('enableRegimeSwitching', checked)}
                  />
                </div>

                <div className="flex items-center justify-between" id="regime-detection-header">
                  <div id="regime-detection-info">
                    <Label className="text-sm font-medium">Automatic Regime Detection</Label>
                    <div className="text-xs text-muted-foreground">
                      Use HMM to detect regimes from historical data
                    </div>
                  </div>
                  <Switch
                    id="regime-detection-toggle"
                    checked={parameters.regimeDetection}
                    onCheckedChange={(checked) => updateParameter('regimeDetection', checked)}
                    disabled={!parameters.enableRegimeSwitching}
                  />
                </div>
              </div>

              <Separator id="advanced-separator-2" />

              {/* Jump Diffusion Parameters */}
              <div className="space-y-4" id="jump-diffusion-section">
                <div className="flex items-center gap-2" id="jump-diffusion-header">
                  <TrendingUpIcon className="h-4 w-4" />
                  <Label className="text-sm font-medium">Jump Diffusion Parameters</Label>
                  <InfoIcon className="h-3 w-3 text-muted-foreground" />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4" id="jump-parameters-grid">
                  <div className="space-y-2" id="jump-intensity-section">
                    <Label htmlFor="jump-intensity" className="text-xs">Jump Intensity</Label>
                    <Slider
                      id="jump-intensity"
                      min={0}
                      max={1}
                      step={0.01}
                      value={[parameters.jumpIntensity]}
                      onValueChange={([value]) => updateParameter('jumpIntensity', value)}
                      className="w-full"
                    />
                    <Badge variant="outline" className="text-xs" id="jump-intensity-display">
                      {parameters.jumpIntensity.toFixed(2)}
                    </Badge>
                  </div>

                  <div className="space-y-2" id="jump-size-mean-section">
                    <Label htmlFor="jump-size-mean" className="text-xs">Jump Size Mean</Label>
                    <Slider
                      id="jump-size-mean"
                      min={-0.20}
                      max={0.20}
                      step={0.01}
                      value={[parameters.jumpSizeMean]}
                      onValueChange={([value]) => updateParameter('jumpSizeMean', value)}
                      className="w-full"
                    />
                    <Badge variant="outline" className="text-xs" id="jump-size-mean-display">
                      {formatPercent(parameters.jumpSizeMean)}
                    </Badge>
                  </div>

                  <div className="space-y-2" id="jump-size-std-section">
                    <Label htmlFor="jump-size-std" className="text-xs">Jump Size Std Dev</Label>
                    <Slider
                      id="jump-size-std"
                      min={0.01}
                      max={0.50}
                      step={0.01}
                      value={[parameters.jumpSizeStd]}
                      onValueChange={([value]) => updateParameter('jumpSizeStd', value)}
                      className="w-full"
                    />
                    <Badge variant="outline" className="text-xs" id="jump-size-std-display">
                      {formatPercent(parameters.jumpSizeStd)}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default SimulationControls;