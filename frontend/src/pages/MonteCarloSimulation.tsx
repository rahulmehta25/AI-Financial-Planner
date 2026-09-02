import React, { useState, useCallback, useEffect } from 'react';
import { toast } from '@/hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Play, 
  StopCircle, 
  Download, 
  GitCompare, 
  History,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  Calculator
} from 'lucide-react';

// Import our components
import SimulationControls, { SimulationParameters } from '@/components/simulation/SimulationControls';
import SimulationResults from '@/components/simulation/SimulationResults';
import ProbabilityChart, { SimulationResult } from '@/components/simulation/ProbabilityChart';

// Import service
import { 
  monteCarloService, 
  MonteCarloRequest, 
  MonteCarloResponse,
  ScenarioComparison 
} from '@/services/monteCarlo';

const MonteCarloSimulation: React.FC = () => {
  // Simulation state
  const [parameters, setParameters] = useState<SimulationParameters>({
    timeHorizon: 30,
    initialInvestment: 100000,
    monthlyContribution: 1000,
    expectedReturn: 0.08,
    volatility: 0.15,
    riskFreeRate: 0.02,
    numSimulations: 10000,
    jumpIntensity: 0.1,
    jumpSizeMean: -0.05,
    jumpSizeStd: 0.2,
    enableRegimeSwitching: false,
    regimeDetection: false,
    targetAmount: undefined,
    successThreshold: 0.95
  });

  const [isRunning, setIsRunning] = useState(false);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  // Scenario comparison state
  const [scenarios, setScenarios] = useState<Array<{
    name: string;
    parameters: SimulationParameters;
    results?: SimulationResult;
  }>>([]);
  const [comparisonResults, setComparisonResults] = useState<ScenarioComparison | null>(null);

  // Validate parameters when they change
  useEffect(() => {
    const validation = monteCarloService.validateParameters(parameters);
    setWarnings(validation.warnings);
    if (!validation.isValid) {
      setError(validation.errors.join(', '));
    } else {
      setError(null);
    }
  }, [parameters]);

  // Transform backend response to frontend format
  const transformResults = useCallback((response: MonteCarloResponse): SimulationResult => {
    const successRate = parameters.targetAmount 
      ? response.final_values.filter(value => value >= parameters.targetAmount!).length / response.final_values.length
      : undefined;

    return {
      finalValues: response.final_values,
      paths: response.paths,
      timestamps: response.timestamps,
      riskMetrics: response.risk_metrics,
      successRate,
      confidenceIntervals: response.confidence_intervals
    };
  }, [parameters.targetAmount]);

  // Run simulation
  const handleRunSimulation = useCallback(async () => {
    try {
      setIsRunning(true);
      setError(null);
      setProgress(0);

      // Validate parameters
      const validation = monteCarloService.validateParameters(parameters);
      if (!validation.isValid) {
        throw new Error(validation.errors.join(', '));
      }

      // Show warnings
      if (validation.warnings.length > 0) {
        validation.warnings.forEach(warning => {
          toast({
            title: "Parameter Warning",
            description: warning,
            variant: "default"
          });
        });
      }

      // Simulate progress for long-running simulations
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 10;
        });
      }, 500);

      toast({
        title: "Simulation Started",
        description: `Running ${parameters.numSimulations.toLocaleString()} Monte Carlo simulations...`
      });

      const request: MonteCarloRequest = parameters;
      const response = await monteCarloService.runSimulation(request);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      const transformedResults = transformResults(response);
      setResults(transformedResults);
      setSimulationId(response.simulation_id);

      toast({
        title: "Simulation Complete",
        description: `Analysis completed in ${response.metadata.computation_time.toFixed(2)} seconds`
      });

    } catch (err: any) {
      setError(err.message);
      toast({
        title: "Simulation Failed",
        description: err.message,
        variant: "destructive"
      });
    } finally {
      setIsRunning(false);
    }
  }, [parameters, transformResults]);

  // Export results
  const handleExportResults = useCallback(async () => {
    if (!simulationId) return;

    try {
      const blob = await monteCarloService.exportResults(simulationId, 'csv');
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `monte-carlo-results-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Export Complete",
        description: "Simulation results exported successfully"
      });
    } catch (err: any) {
      toast({
        title: "Export Failed",
        description: err.message,
        variant: "destructive"
      });
    }
  }, [simulationId]);

  // Add to scenario comparison
  const handleAddToComparison = useCallback(() => {
    if (!results) return;

    const scenarioName = `Scenario ${scenarios.length + 1}`;
    setScenarios(prev => [...prev, {
      name: scenarioName,
      parameters: { ...parameters },
      results
    }]);

    toast({
      title: "Scenario Added",
      description: `Added ${scenarioName} to comparison`
    });
  }, [parameters, results, scenarios.length]);

  // Load preset parameters
  const handleLoadPreset = useCallback((assetClass: 'stocks' | 'bonds' | 'mixed' | 'aggressive') => {
    const suggested = monteCarloService.getSuggestedParameters(assetClass);
    setParameters(prev => ({ ...prev, ...suggested }));
    
    toast({
      title: "Preset Loaded",
      description: `Loaded ${assetClass} asset class parameters`
    });
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="container mx-auto p-6 space-y-6" id="monte-carlo-simulation-page">
      {/* Header */}
      <div className="flex items-center justify-between" id="page-header">
        <div id="page-title-section">
          <h1 className="text-3xl font-bold flex items-center gap-3" id="page-title">
            <Calculator className="h-8 w-8 text-blue-600" />
            Monte Carlo Simulation
          </h1>
          <p className="text-muted-foreground mt-2" id="page-description">
            Advanced portfolio simulation with statistical analysis and risk modeling
          </p>
        </div>

        <div className="flex gap-2" id="page-actions">
          <Button 
            variant="outline" 
            onClick={() => handleLoadPreset('mixed')}
            id="load-preset-button"
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Load Preset
          </Button>
          {results && (
            <Button 
              variant="outline" 
              onClick={handleAddToComparison}
              id="add-to-comparison-button"
            >
              <GitCompare className="h-4 w-4 mr-2" />
              Add to Comparison
            </Button>
          )}
        </div>
      </div>

      {/* Status and Warnings */}
      {(error || warnings.length > 0 || isRunning) && (
        <div className="space-y-2" id="status-section">
          {error && (
            <Alert variant="destructive" id="error-alert">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {warnings.map((warning, index) => (
            <Alert key={index} id={`warning-alert-${index}`}>
              <Info className="h-4 w-4" />
              <AlertDescription>{warning}</AlertDescription>
            </Alert>
          ))}
          
          {isRunning && (
            <Alert id="running-alert">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="flex items-center justify-between" id="progress-content">
                  <span>Running simulation...</span>
                  <Badge variant="outline" id="progress-badge">{progress.toFixed(0)}%</Badge>
                </div>
                <Progress value={progress} className="mt-2" id="simulation-progress" />
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6" id="main-content-grid">
        {/* Controls Panel */}
        <div className="xl:col-span-1" id="controls-panel">
          <SimulationControls
            parameters={parameters}
            onParametersChange={setParameters}
            onRunSimulation={handleRunSimulation}
            isRunning={isRunning}
            className="sticky top-6"
          />
        </div>

        {/* Results Panel */}
        <div className="xl:col-span-2 space-y-6" id="results-panel">
          {/* Quick Stats */}
          {results && (
            <Card id="quick-stats-card">
              <CardHeader id="quick-stats-header">
                <CardTitle className="flex items-center gap-2" id="quick-stats-title">
                  <TrendingUp className="h-5 w-5" />
                  Simulation Summary
                </CardTitle>
              </CardHeader>
              <CardContent id="quick-stats-content">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4" id="quick-stats-grid">
                  <div className="text-center" id="mean-outcome">
                    <div className="text-sm text-muted-foreground">Expected Value</div>
                    <div className="text-lg font-semibold">
                      {formatCurrency(results.finalValues.reduce((a, b) => a + b, 0) / results.finalValues.length)}
                    </div>
                  </div>
                  <div className="text-center" id="success-rate">
                    <div className="text-sm text-muted-foreground">Success Rate</div>
                    <div className="text-lg font-semibold">
                      {results.successRate ? `${(results.successRate * 100).toFixed(1)}%` : 'N/A'}
                    </div>
                  </div>
                  <div className="text-center" id="var-metric">
                    <div className="text-sm text-muted-foreground">VaR (95%)</div>
                    <div className="text-lg font-semibold">
                      {formatCurrency(results.riskMetrics['Value at Risk (95%)'])}
                    </div>
                  </div>
                  <div className="text-center" id="sharpe-ratio">
                    <div className="text-sm text-muted-foreground">Sharpe Ratio</div>
                    <div className="text-lg font-semibold">
                      {results.riskMetrics['Sharpe Ratio'].toFixed(2)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Simulation Results */}
          <SimulationResults 
            results={results}
            targetAmount={parameters.targetAmount}
            onExportResults={simulationId ? handleExportResults : undefined}
          />

          {/* Probability Analysis */}
          <ProbabilityChart 
            results={results}
            targetAmount={parameters.targetAmount}
          />
        </div>
      </div>

      {/* Scenario Comparison */}
      {scenarios.length > 0 && (
        <>
          <Separator id="scenario-separator" />
          <Card id="scenario-comparison-card">
            <CardHeader id="scenario-comparison-header">
              <CardTitle className="flex items-center gap-2" id="scenario-comparison-title">
                <GitCompare className="h-5 w-5" />
                Scenario Comparison
              </CardTitle>
              <CardDescription id="scenario-comparison-description">
                Compare different simulation scenarios side by side
              </CardDescription>
            </CardHeader>
            <CardContent id="scenario-comparison-content">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="scenarios-grid">
                {scenarios.map((scenario, index) => (
                  <Card key={index} className="p-4" id={`scenario-card-${index}`}>
                    <div className="flex items-center justify-between mb-2" id={`scenario-header-${index}`}>
                      <h4 className="font-semibold">{scenario.name}</h4>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={() => setScenarios(prev => prev.filter((_, i) => i !== index))}
                        id={`remove-scenario-${index}`}
                      >
                        Remove
                      </Button>
                    </div>
                    
                    <div className="space-y-2 text-sm" id={`scenario-details-${index}`}>
                      <div className="flex justify-between" id={`scenario-investment-${index}`}>
                        <span>Initial Investment:</span>
                        <span>{formatCurrency(scenario.parameters.initialInvestment)}</span>
                      </div>
                      <div className="flex justify-between" id={`scenario-return-${index}`}>
                        <span>Expected Return:</span>
                        <span>{(scenario.parameters.expectedReturn * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between" id={`scenario-volatility-${index}`}>
                        <span>Volatility:</span>
                        <span>{(scenario.parameters.volatility * 100).toFixed(1)}%</span>
                      </div>
                      {scenario.results && (
                        <>
                          <Separator className="my-2" id={`scenario-separator-${index}`} />
                          <div className="flex justify-between font-medium" id={`scenario-expected-${index}`}>
                            <span>Expected Value:</span>
                            <span>
                              {formatCurrency(
                                scenario.results.finalValues.reduce((a, b) => a + b, 0) / scenario.results.finalValues.length
                              )}
                            </span>
                          </div>
                          {scenario.results.successRate && (
                            <div className="flex justify-between" id={`scenario-success-${index}`}>
                              <span>Success Rate:</span>
                              <span>{(scenario.results.successRate * 100).toFixed(1)}%</span>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
              
              {scenarios.length >= 2 && (
                <div className="mt-4" id="compare-scenarios-section">
                  <Button 
                    onClick={() => {
                      // TODO: Implement scenario comparison analysis
                      toast({
                        title: "Feature Coming Soon",
                        description: "Detailed scenario comparison will be available in the next update"
                      });
                    }}
                    className="w-full"
                    id="compare-scenarios-button"
                  >
                    <GitCompare className="h-4 w-4 mr-2" />
                    Run Detailed Comparison Analysis
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Asset Class Presets */}
      <Card id="presets-card">
        <CardHeader id="presets-header">
          <CardTitle>Parameter Presets</CardTitle>
          <CardDescription>
            Quick start with pre-configured parameters for different asset classes
          </CardDescription>
        </CardHeader>
        <CardContent id="presets-content">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4" id="presets-grid">
            {[
              { key: 'stocks', name: 'Stocks', desc: 'High growth, high volatility' },
              { key: 'bonds', name: 'Bonds', desc: 'Low risk, stable returns' },
              { key: 'mixed', name: 'Balanced', desc: '60/40 stocks/bonds mix' },
              { key: 'aggressive', name: 'Aggressive', desc: 'Maximum growth potential' }
            ].map(preset => (
              <Button
                key={preset.key}
                variant="outline"
                className="h-auto p-4 flex flex-col items-start"
                onClick={() => handleLoadPreset(preset.key as any)}
                id={`preset-${preset.key}`}
              >
                <div className="font-medium">{preset.name}</div>
                <div className="text-xs text-muted-foreground mt-1">{preset.desc}</div>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MonteCarloSimulation;