import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { 
  Settings, 
  Leaf, 
  TrendingUp, 
  Shield, 
  Globe, 
  Factory, 
  Zap, 
  Home, 
  Briefcase,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  RotateCcw
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ESGConstraints {
  enabled: boolean;
  minESGScore: number;
  excludeSectors: string[];
  sustainabilityFocus: 'none' | 'moderate' | 'high';
  carbonNeutralOnly: boolean;
  socialImpactWeight: number;
  governanceWeight: number;
}

interface SectorConstraints {
  enabled: boolean;
  sectors: {
    [key: string]: {
      min: number;
      max: number;
      current: number;
      enabled: boolean;
    };
  };
}

interface RiskConstraints {
  maxRisk: number;
  minReturn: number;
  maxDrawdown: number;
  concentrationLimit: number;
  rebalanceThreshold: number;
}

interface OptimizationConstraints {
  esg: ESGConstraints;
  sectors: SectorConstraints;
  risk: RiskConstraints;
  customConstraints: string[];
}

interface ConstraintsPanelProps {
  id?: string;
  constraints?: OptimizationConstraints;
  onConstraintsChange?: (constraints: OptimizationConstraints) => void;
  className?: string;
}

const SECTORS = [
  { id: 'technology', name: 'Technology', icon: Zap, color: '#3b82f6' },
  { id: 'healthcare', name: 'Healthcare', icon: Shield, color: '#10b981' },
  { id: 'financial', name: 'Financial', icon: DollarSign, color: '#f59e0b' },
  { id: 'consumer', name: 'Consumer Discretionary', icon: Briefcase, color: '#ef4444' },
  { id: 'industrials', name: 'Industrials', icon: Factory, color: '#8b5cf6' },
  { id: 'energy', name: 'Energy', icon: Zap, color: '#f97316' },
  { id: 'utilities', name: 'Utilities', icon: Home, color: '#06b6d4' },
  { id: 'materials', name: 'Materials', icon: Globe, color: '#84cc16' },
  { id: 'real_estate', name: 'Real Estate', icon: Home, color: '#ec4899' },
  { id: 'communication', name: 'Communication', icon: Globe, color: '#6366f1' }
];

const ESG_EXCLUDED_SECTORS = [
  'tobacco',
  'weapons',
  'fossil_fuels',
  'gambling',
  'alcohol',
  'adult_entertainment',
  'controversial_weapons'
];

export const ConstraintsPanel: React.FC<ConstraintsPanelProps> = ({
  id = "constraints-panel",
  constraints: initialConstraints,
  onConstraintsChange,
  className = ""
}) => {
  const { toast } = useToast();
  
  const [constraints, setConstraints] = useState<OptimizationConstraints>({
    esg: {
      enabled: false,
      minESGScore: 5,
      excludeSectors: [],
      sustainabilityFocus: 'none',
      carbonNeutralOnly: false,
      socialImpactWeight: 20,
      governanceWeight: 30
    },
    sectors: {
      enabled: true,
      sectors: SECTORS.reduce((acc, sector) => ({
        ...acc,
        [sector.id]: {
          min: 0,
          max: 30,
          current: 10,
          enabled: true
        }
      }), {})
    },
    risk: {
      maxRisk: 15,
      minReturn: 5,
      maxDrawdown: 20,
      concentrationLimit: 25,
      rebalanceThreshold: 5
    },
    customConstraints: []
  });

  useEffect(() => {
    if (initialConstraints) {
      setConstraints(initialConstraints);
    }
  }, [initialConstraints]);

  const updateConstraints = (newConstraints: OptimizationConstraints) => {
    setConstraints(newConstraints);
    onConstraintsChange?.(newConstraints);
  };

  const updateESGConstraints = (updates: Partial<ESGConstraints>) => {
    updateConstraints({
      ...constraints,
      esg: { ...constraints.esg, ...updates }
    });
  };

  const updateSectorConstraints = (updates: Partial<SectorConstraints>) => {
    updateConstraints({
      ...constraints,
      sectors: { ...constraints.sectors, ...updates }
    });
  };

  const updateRiskConstraints = (updates: Partial<RiskConstraints>) => {
    updateConstraints({
      ...constraints,
      risk: { ...constraints.risk, ...updates }
    });
  };

  const updateSectorLimit = (sectorId: string, field: 'min' | 'max', value: number) => {
    const newSectors = {
      ...constraints.sectors.sectors,
      [sectorId]: {
        ...constraints.sectors.sectors[sectorId],
        [field]: value
      }
    };
    updateSectorConstraints({ sectors: newSectors });
  };

  const toggleESGExclusion = (sector: string) => {
    const excludeSectors = constraints.esg.excludeSectors.includes(sector)
      ? constraints.esg.excludeSectors.filter(s => s !== sector)
      : [...constraints.esg.excludeSectors, sector];
    
    updateESGConstraints({ excludeSectors });
  };

  const resetConstraints = () => {
    const defaultConstraints: OptimizationConstraints = {
      esg: {
        enabled: false,
        minESGScore: 5,
        excludeSectors: [],
        sustainabilityFocus: 'none',
        carbonNeutralOnly: false,
        socialImpactWeight: 20,
        governanceWeight: 30
      },
      sectors: {
        enabled: true,
        sectors: SECTORS.reduce((acc, sector) => ({
          ...acc,
          [sector.id]: {
            min: 0,
            max: 30,
            current: 10,
            enabled: true
          }
        }), {})
      },
      risk: {
        maxRisk: 15,
        minReturn: 5,
        maxDrawdown: 20,
        concentrationLimit: 25,
        rebalanceThreshold: 5
      },
      customConstraints: []
    };
    
    updateConstraints(defaultConstraints);
    toast({
      title: "Constraints Reset",
      description: "All constraints have been reset to default values.",
    });
  };

  const getConstraintsSummary = () => {
    let activeCount = 0;
    if (constraints.esg.enabled) activeCount++;
    if (constraints.sectors.enabled) activeCount++;
    if (constraints.risk.maxRisk < 20) activeCount++;
    return activeCount;
  };

  return (
    <Card id={id} className={`glass border-white/10 ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-primary" />
            Optimization Constraints
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="glass border-white/20">
              {getConstraintsSummary()} active
            </Badge>
            <Button
              id="reset-constraints-btn"
              variant="ghost"
              size="sm"
              onClick={resetConstraints}
            >
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        </CardTitle>
        <CardDescription>
          Configure investment preferences and risk limits
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="esg" className="w-full">
          <TabsList id="constraints-tabs" className="grid w-full grid-cols-3 glass">
            <TabsTrigger value="esg" className="flex items-center gap-2">
              <Leaf className="w-4 h-4" />
              ESG
            </TabsTrigger>
            <TabsTrigger value="sectors" className="flex items-center gap-2">
              <Factory className="w-4 h-4" />
              Sectors
            </TabsTrigger>
            <TabsTrigger value="risk" className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Risk
            </TabsTrigger>
          </TabsList>

          {/* ESG Constraints */}
          <TabsContent value="esg" className="space-y-6 mt-6">
            <div id="esg-constraints" className="space-y-4">
              {/* ESG Toggle */}
              <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10">
                <div className="flex items-center gap-3">
                  <Leaf className="w-5 h-5 text-green-500" />
                  <div>
                    <Label className="text-sm font-medium">Enable ESG Screening</Label>
                    <p className="text-xs text-muted-foreground">Apply environmental, social, and governance filters</p>
                  </div>
                </div>
                <Switch
                  id="esg-enabled"
                  checked={constraints.esg.enabled}
                  onCheckedChange={(enabled) => updateESGConstraints({ enabled })}
                />
              </div>

              {constraints.esg.enabled && (
                <>
                  {/* ESG Score Minimum */}
                  <div id="esg-score-container" className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label className="text-sm font-medium">Minimum ESG Score</Label>
                      <Badge variant="outline" className="bg-white/10">
                        {constraints.esg.minESGScore}/10
                      </Badge>
                    </div>
                    <Slider
                      id="esg-min-score"
                      value={[constraints.esg.minESGScore]}
                      onValueChange={([value]) => updateESGConstraints({ minESGScore: value })}
                      max={10}
                      min={1}
                      step={0.5}
                      className="w-full"
                    />
                    <p className="text-xs text-muted-foreground">
                      Only include investments with ESG scores above this threshold
                    </p>
                  </div>

                  <Separator className="bg-white/10" />

                  {/* Sustainability Focus */}
                  <div id="sustainability-focus-container" className="space-y-3">
                    <Label className="text-sm font-medium">Sustainability Focus</Label>
                    <Select
                      value={constraints.esg.sustainabilityFocus}
                      onValueChange={(value: 'none' | 'moderate' | 'high') => 
                        updateESGConstraints({ sustainabilityFocus: value })
                      }
                    >
                      <SelectTrigger id="sustainability-focus" className="glass">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="moderate">Moderate</SelectItem>
                        <SelectItem value="high">High Priority</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Carbon Neutral Toggle */}
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Carbon Neutral Only</Label>
                    <Switch
                      id="carbon-neutral-only"
                      checked={constraints.esg.carbonNeutralOnly}
                      onCheckedChange={(carbonNeutralOnly) => updateESGConstraints({ carbonNeutralOnly })}
                    />
                  </div>

                  <Separator className="bg-white/10" />

                  {/* Excluded Sectors */}
                  <div id="excluded-sectors-container" className="space-y-3">
                    <Label className="text-sm font-medium">Excluded Sectors</Label>
                    <div className="grid grid-cols-2 gap-2">
                      {ESG_EXCLUDED_SECTORS.map((sector) => (
                        <div
                          key={sector}
                          className={`p-2 rounded-lg border cursor-pointer transition-colors ${
                            constraints.esg.excludeSectors.includes(sector)
                              ? 'bg-red-500/20 border-red-500/50'
                              : 'bg-white/5 border-white/10 hover:bg-white/10'
                          }`}
                          onClick={() => toggleESGExclusion(sector)}
                        >
                          <div className="flex items-center gap-2">
                            {constraints.esg.excludeSectors.includes(sector) ? (
                              <AlertTriangle className="w-4 h-4 text-red-500" />
                            ) : (
                              <div className="w-4 h-4" />
                            )}
                            <span className="text-sm capitalize">
                              {sector.replace('_', ' ')}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* ESG Weights */}
                  <div id="esg-weights-container" className="space-y-4">
                    <Label className="text-sm font-medium">ESG Component Weights</Label>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <Label className="text-xs">Social Impact Weight</Label>
                          <span className="text-xs text-muted-foreground">{constraints.esg.socialImpactWeight}%</span>
                        </div>
                        <Slider
                          id="social-impact-weight"
                          value={[constraints.esg.socialImpactWeight]}
                          onValueChange={([value]) => updateESGConstraints({ socialImpactWeight: value })}
                          max={50}
                          min={0}
                          step={5}
                        />
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <Label className="text-xs">Governance Weight</Label>
                          <span className="text-xs text-muted-foreground">{constraints.esg.governanceWeight}%</span>
                        </div>
                        <Slider
                          id="governance-weight"
                          value={[constraints.esg.governanceWeight]}
                          onValueChange={([value]) => updateESGConstraints({ governanceWeight: value })}
                          max={50}
                          min={0}
                          step={5}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </TabsContent>

          {/* Sector Constraints */}
          <TabsContent value="sectors" className="space-y-6 mt-6">
            <div id="sector-constraints" className="space-y-4">
              {/* Sector Constraints Toggle */}
              <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10">
                <div className="flex items-center gap-3">
                  <Factory className="w-5 h-5 text-blue-500" />
                  <div>
                    <Label className="text-sm font-medium">Enable Sector Limits</Label>
                    <p className="text-xs text-muted-foreground">Control maximum allocation per sector</p>
                  </div>
                </div>
                <Switch
                  id="sectors-enabled"
                  checked={constraints.sectors.enabled}
                  onCheckedChange={(enabled) => updateSectorConstraints({ enabled })}
                />
              </div>

              {constraints.sectors.enabled && (
                <div id="sector-limits-container" className="space-y-4">
                  {SECTORS.map((sector) => {
                    const sectorData = constraints.sectors.sectors[sector.id];
                    const IconComponent = sector.icon;
                    
                    return (
                      <div key={sector.id} className="p-4 rounded-lg bg-white/5 border border-white/10">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <IconComponent className="w-4 h-4" style={{ color: sector.color }} />
                            <span className="text-sm font-medium">{sector.name}</span>
                          </div>
                          <Badge variant="outline" className="bg-white/10 text-xs">
                            {sectorData.min}% - {sectorData.max}%
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label className="text-xs text-muted-foreground">Min %</Label>
                            <Input
                              id={`${sector.id}-min`}
                              type="number"
                              value={sectorData.min}
                              onChange={(e) => updateSectorLimit(sector.id, 'min', parseFloat(e.target.value) || 0)}
                              className="h-8 text-xs glass"
                              min="0"
                              max="100"
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-muted-foreground">Max %</Label>
                            <Input
                              id={`${sector.id}-max`}
                              type="number"
                              value={sectorData.max}
                              onChange={(e) => updateSectorLimit(sector.id, 'max', parseFloat(e.target.value) || 0)}
                              className="h-8 text-xs glass"
                              min="0"
                              max="100"
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Risk Constraints */}
          <TabsContent value="risk" className="space-y-6 mt-6">
            <div id="risk-constraints" className="space-y-4">
              {/* Maximum Risk */}
              <div id="max-risk-container" className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    <Shield className="w-4 h-4 text-orange-500" />
                    Maximum Risk (Volatility)
                  </Label>
                  <Badge variant="outline" className="bg-white/10">
                    {constraints.risk.maxRisk}%
                  </Badge>
                </div>
                <Slider
                  id="max-risk"
                  value={[constraints.risk.maxRisk]}
                  onValueChange={([value]) => updateRiskConstraints({ maxRisk: value })}
                  max={30}
                  min={5}
                  step={0.5}
                  className="w-full"
                />
              </div>

              {/* Minimum Return */}
              <div id="min-return-container" className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-green-500" />
                    Minimum Expected Return
                  </Label>
                  <Badge variant="outline" className="bg-white/10">
                    {constraints.risk.minReturn}%
                  </Badge>
                </div>
                <Slider
                  id="min-return"
                  value={[constraints.risk.minReturn]}
                  onValueChange={([value]) => updateRiskConstraints({ minReturn: value })}
                  max={15}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
              </div>

              <Separator className="bg-white/10" />

              {/* Maximum Drawdown */}
              <div id="max-drawdown-container" className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Maximum Drawdown</Label>
                  <Badge variant="outline" className="bg-white/10">
                    {constraints.risk.maxDrawdown}%
                  </Badge>
                </div>
                <Slider
                  id="max-drawdown"
                  value={[constraints.risk.maxDrawdown]}
                  onValueChange={([value]) => updateRiskConstraints({ maxDrawdown: value })}
                  max={50}
                  min={5}
                  step={1}
                  className="w-full"
                />
              </div>

              {/* Concentration Limit */}
              <div id="concentration-limit-container" className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Single Asset Limit</Label>
                  <Badge variant="outline" className="bg-white/10">
                    {constraints.risk.concentrationLimit}%
                  </Badge>
                </div>
                <Slider
                  id="concentration-limit"
                  value={[constraints.risk.concentrationLimit]}
                  onValueChange={([value]) => updateRiskConstraints({ concentrationLimit: value })}
                  max={50}
                  min={5}
                  step={1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Maximum percentage any single asset can represent
                </p>
              </div>

              {/* Rebalance Threshold */}
              <div id="rebalance-threshold-container" className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Rebalance Threshold</Label>
                  <Badge variant="outline" className="bg-white/10">
                    {constraints.risk.rebalanceThreshold}%
                  </Badge>
                </div>
                <Slider
                  id="rebalance-threshold"
                  value={[constraints.risk.rebalanceThreshold]}
                  onValueChange={([value]) => updateRiskConstraints({ rebalanceThreshold: value })}
                  max={20}
                  min={1}
                  step={0.5}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Trigger rebalancing when allocation drifts by this percentage
                </p>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Constraints Summary */}
        <div id="constraints-summary" className="mt-6 p-4 rounded-lg bg-white/5 border border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <Label className="text-sm font-medium">Active Constraints Summary</Label>
          </div>
          <div className="space-y-2 text-xs text-muted-foreground">
            {constraints.esg.enabled && (
              <p>• ESG screening enabled (min score: {constraints.esg.minESGScore}/10)</p>
            )}
            {constraints.sectors.enabled && (
              <p>• Sector allocation limits applied</p>
            )}
            <p>• Maximum risk: {constraints.risk.maxRisk}%</p>
            <p>• Minimum return: {constraints.risk.minReturn}%</p>
            <p>• Max single asset: {constraints.risk.concentrationLimit}%</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ConstraintsPanel;