import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  TrendingUp, 
  PieChart, 
  Settings, 
  Play, 
  RefreshCw, 
  Download, 
  Share2,
  CheckCircle,
  AlertTriangle,
  Target,
  BarChart3,
  Zap
} from 'lucide-react';

import EfficientFrontier from '@/components/optimization/EfficientFrontier';
import AllocationChart from '@/components/optimization/AllocationChart';
import ConstraintsPanel from '@/components/optimization/ConstraintsPanel';

import { optimizationService, OptimizationRequest, OptimizationResult, PortfolioPoint } from '@/services/optimization';
import { useToast } from '@/hooks/use-toast';

interface AssetAllocation {
  id: string;
  name: string;
  symbol: string;
  percentage: number;
  color: string;
  locked?: boolean;
  expectedReturn?: number;
  risk?: number;
}

interface OptimizationState {
  isLoading: boolean;
  isOptimizing: boolean;
  result?: OptimizationResult;
  error?: string;
  progress: number;
}

const PortfolioOptimizer = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  // State management
  const [optimizationState, setOptimizationState] = useState<OptimizationState>({
    isLoading: false,
    isOptimizing: false,
    progress: 0
  });

  const [selectedPortfolio, setSelectedPortfolio] = useState<PortfolioPoint | null>(null);
  const [currentAllocations, setCurrentAllocations] = useState<AssetAllocation[]>([]);
  const [optimizedAllocations, setOptimizedAllocations] = useState<AssetAllocation[]>([]);
  const [constraints, setConstraints] = useState({
    esg: {
      enabled: false,
      minESGScore: 5,
      excludeSectors: [],
      sustainabilityFocus: 'none' as const,
      carbonNeutralOnly: false,
      socialImpactWeight: 20,
      governanceWeight: 30
    },
    sectors: {
      enabled: true,
      sectors: {}
    },
    risk: {
      maxRisk: 15,
      minReturn: 5,
      maxDrawdown: 20,
      concentrationLimit: 25,
      rebalanceThreshold: 5
    }
  });

  const [riskTolerance, setRiskTolerance] = useState(5);
  const [targetReturn, setTargetReturn] = useState(8);
  const [comparisonMode, setComparisonMode] = useState(false);

  // Initialize with mock current portfolio
  useEffect(() => {
    const mockCurrentAllocations: AssetAllocation[] = [
      { id: '1', name: 'US Stocks', symbol: 'VTI', percentage: 35, color: '#3b82f6', expectedReturn: 8.5, risk: 18 },
      { id: '2', name: 'International Stocks', symbol: 'VTIAX', percentage: 15, color: '#10b981', expectedReturn: 7.2, risk: 20 },
      { id: '3', name: 'Bonds', symbol: 'BND', percentage: 35, color: '#f59e0b', expectedReturn: 4.1, risk: 6 },
      { id: '4', name: 'REITs', symbol: 'VNQ', percentage: 10, color: '#ef4444', expectedReturn: 6.8, risk: 22 },
      { id: '5', name: 'Cash', symbol: 'VMFXX', percentage: 5, color: '#8b5cf6', expectedReturn: 2.1, risk: 1 }
    ];
    setCurrentAllocations(mockCurrentAllocations);
  }, []);

  // Optimization workflow
  const runOptimization = useCallback(async () => {
    try {
      setOptimizationState(prev => ({ 
        ...prev, 
        isOptimizing: true, 
        progress: 0, 
        error: undefined 
      }));

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setOptimizationState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90)
        }));
      }, 200);

      const request: OptimizationRequest = {
        constraints,
        preferences: {
          riskTolerance,
          targetReturn,
          timeHorizon: 10, // years
          liquidityNeeds: 0.1
        },
        currentPortfolio: {
          holdings: currentAllocations.map(alloc => ({
            symbol: alloc.symbol,
            shares: 100,
            currentPrice: 100,
            allocation: alloc.percentage
          }))
        }
      };

      const result = await optimizationService.optimizePortfolio(request);
      
      clearInterval(progressInterval);
      
      // Convert optimization result to allocation format
      const newOptimizedAllocations: AssetAllocation[] = result.recommendedAllocation.assets.map((asset, index) => ({
        id: (index + 1).toString(),
        name: asset.name,
        symbol: asset.symbol,
        percentage: asset.allocation,
        color: currentAllocations.find(a => a.symbol === asset.symbol)?.color || '#64748b',
        expectedReturn: asset.expectedReturn,
        risk: asset.risk
      }));

      setOptimizedAllocations(newOptimizedAllocations);
      
      setOptimizationState({
        isLoading: false,
        isOptimizing: false,
        result,
        progress: 100
      });

      toast({
        title: "Optimization Complete",
        description: `Found optimal portfolio with ${result.recommendedAllocation.sharpeRatio.toFixed(2)} Sharpe ratio`,
      });

    } catch (error: any) {
      setOptimizationState(prev => ({
        ...prev,
        isOptimizing: false,
        error: error.message,
        progress: 0
      }));

      toast({
        title: "Optimization Failed",
        description: error.message,
        variant: "destructive",
      });
    }
  }, [constraints, riskTolerance, targetReturn, currentAllocations, toast]);

  const handlePortfolioPointSelect = (portfolio: PortfolioPoint) => {
    setSelectedPortfolio(portfolio);
    
    // Convert portfolio weights to allocations
    const newAllocations: AssetAllocation[] = Object.entries(portfolio.weights).map(([symbol, weight], index) => {
      const existing = currentAllocations.find(a => a.symbol === symbol);
      return {
        id: (index + 1).toString(),
        name: existing?.name || symbol,
        symbol,
        percentage: Number((weight * 100).toFixed(1)),
        color: existing?.color || '#64748b',
        expectedReturn: existing?.expectedReturn || 8,
        risk: existing?.risk || 15
      };
    });

    setOptimizedAllocations(newAllocations);
  };

  const handleRiskReturnChange = (risk: number, expectedReturn: number) => {
    setRiskTolerance(risk);
    setTargetReturn(expectedReturn);
  };

  const executeRebalancing = async () => {
    try {
      const plan = await optimizationService.generateRebalancingPlan(
        currentAllocations.map(alloc => ({
          symbol: alloc.symbol,
          shares: 100,
          currentPrice: 100
        })),
        optimizedAllocations.map(alloc => ({
          symbol: alloc.symbol,
          targetAllocation: alloc.percentage
        }))
      );

      const result = await optimizationService.executeRebalancing(plan);
      
      if (result.success) {
        setCurrentAllocations(optimizedAllocations);
        toast({
          title: "Rebalancing Complete",
          description: `Successfully executed ${result.executedTransactions} transactions`,
        });
      }
    } catch (error: any) {
      toast({
        title: "Rebalancing Failed",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const calculateCurrentMetrics = () => {
    if (currentAllocations.length === 0) return null;
    
    return optimizationService.calculatePortfolioMetrics(
      currentAllocations.map(alloc => ({
        symbol: alloc.symbol,
        allocation: alloc.percentage,
        expectedReturn: alloc.expectedReturn || 8,
        risk: alloc.risk || 15
      }))
    );
  };

  const calculateOptimizedMetrics = () => {
    if (optimizedAllocations.length === 0) return null;
    
    return optimizationService.calculatePortfolioMetrics(
      optimizedAllocations.map(alloc => ({
        symbol: alloc.symbol,
        allocation: alloc.percentage,
        expectedReturn: alloc.expectedReturn || 8,
        risk: alloc.risk || 15
      }))
    );
  };

  const currentMetrics = calculateCurrentMetrics();
  const optimizedMetrics = calculateOptimizedMetrics();

  if (optimizationState.isLoading) {
    return (
      <div id="optimizer-loading" className="">
        
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
          <div className="space-y-6">
            <Skeleton className="h-10 w-64" />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Skeleton className="h-96" />
              <Skeleton className="h-96" />
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div id="portfolio-optimizer-page" className="">
      
      <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
        {/* Header */}
        <div id="optimizer-header" className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success mb-2">
                Portfolio Optimizer
              </h1>
              <p className="text-lg text-muted-foreground">
                {user ? `Welcome ${user.firstName}, ` : ''}optimize your portfolio for maximum risk-adjusted returns
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                id="comparison-toggle"
                variant="outline"
                onClick={() => setComparisonMode(!comparisonMode)}
                className="glass border-white/20"
              >
                <BarChart3 className="w-4 h-4 mr-2" />
                {comparisonMode ? 'Single View' : 'Compare'}
              </Button>
              
              <Button
                id="run-optimization-btn"
                onClick={runOptimization}
                disabled={optimizationState.isOptimizing}
                className="bg-gradient-to-r from-primary to-success hover:shadow-glow transition-all duration-300"
              >
                {optimizationState.isOptimizing ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Zap className="w-4 h-4 mr-2" />
                )}
                {optimizationState.isOptimizing ? 'Optimizing...' : 'Optimize Portfolio'}
              </Button>
            </div>
          </div>

          {/* Optimization Progress */}
          {optimizationState.isOptimizing && (
            <div id="optimization-progress" className="mb-6">
              <Card className="glass border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Optimizing Portfolio</span>
                        <span className="text-sm text-muted-foreground">{optimizationState.progress}%</span>
                      </div>
                      <Progress value={optimizationState.progress} className="h-2" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Error Display */}
          {optimizationState.error && (
            <Alert variant="destructive" className="mb-6">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{optimizationState.error}</AlertDescription>
            </Alert>
          )}
        </div>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Portfolio Metrics Comparison */}
          {(currentMetrics || optimizedMetrics) && (
            <div id="metrics-comparison" className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Current Portfolio Metrics */}
              {currentMetrics && (
                <Card className="glass border-white/10">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500" />
                      Current Portfolio
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Expected Return</span>
                      <span className="text-sm font-medium">{currentMetrics.expectedReturn.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Risk</span>
                      <span className="text-sm font-medium">{currentMetrics.risk.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
                      <span className="text-sm font-medium">{currentMetrics.sharpeRatio.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Optimized Portfolio Metrics */}
              {optimizedMetrics && (
                <Card className="glass border-white/10">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500" />
                      Optimized Portfolio
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Expected Return</span>
                      <span className="text-sm font-medium text-green-500">{optimizedMetrics.expectedReturn.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Risk</span>
                      <span className="text-sm font-medium">{optimizedMetrics.risk.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
                      <span className="text-sm font-medium text-green-500">{optimizedMetrics.sharpeRatio.toFixed(2)}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Improvement Metrics */}
              {currentMetrics && optimizedMetrics && (
                <Card className="glass border-white/10">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-success" />
                      Improvement
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Return Increase</span>
                      <span className="text-sm font-medium text-success">
                        +{(optimizedMetrics.expectedReturn - currentMetrics.expectedReturn).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Risk Change</span>
                      <span className={`text-sm font-medium ${
                        optimizedMetrics.risk < currentMetrics.risk ? 'text-success' : 'text-warning'
                      }`}>
                        {optimizedMetrics.risk < currentMetrics.risk ? '' : '+'}
                        {(optimizedMetrics.risk - currentMetrics.risk).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Sharpe Improvement</span>
                      <span className="text-sm font-medium text-success">
                        +{(optimizedMetrics.sharpeRatio - currentMetrics.sharpeRatio).toFixed(2)}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Main Content Tabs */}
          <Tabs defaultValue="visualization" className="w-full">
            <TabsList id="optimizer-tabs" className="grid w-full grid-cols-3 glass">
              <TabsTrigger value="visualization" className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Visualization
              </TabsTrigger>
              <TabsTrigger value="allocations" className="flex items-center gap-2">
                <PieChart className="w-4 h-4" />
                Allocations
              </TabsTrigger>
              <TabsTrigger value="constraints" className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Constraints
              </TabsTrigger>
            </TabsList>

            {/* Efficient Frontier Visualization */}
            <TabsContent value="visualization" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 xl:grid-cols-1 gap-6">
                <EfficientFrontier
                  portfolioData={optimizationState.result?.efficientFrontier.portfolios}
                  currentPortfolio={optimizationState.result?.efficientFrontier.currentPortfolio}
                  onPointSelect={handlePortfolioPointSelect}
                  onRiskReturnChange={handleRiskReturnChange}
                />
              </div>
            </TabsContent>

            {/* Asset Allocations */}
            <TabsContent value="allocations" className="space-y-6 mt-6">
              <div className={`grid grid-cols-1 ${comparisonMode ? 'lg:grid-cols-2' : 'lg:grid-cols-1'} gap-6`}>
                {/* Current Portfolio */}
                <AllocationChart
                  id="current-allocation-chart"
                  allocations={currentAllocations}
                  onAllocationChange={setCurrentAllocations}
                  editable={true}
                  showControls={true}
                />

                {/* Optimized Portfolio */}
                {(comparisonMode || optimizedAllocations.length > 0) && (
                  <AllocationChart
                    id="optimized-allocation-chart"
                    allocations={optimizedAllocations}
                    onAllocationChange={setOptimizedAllocations}
                    editable={false}
                    showControls={false}
                    className={optimizedAllocations.length > 0 ? 'border-green-500/30' : ''}
                  />
                )}
              </div>

              {/* Rebalancing Actions */}
              {optimizedAllocations.length > 0 && (
                <div id="rebalancing-actions" className="flex justify-center gap-3">
                  <Button
                    id="execute-rebalancing-btn"
                    onClick={executeRebalancing}
                    className="bg-gradient-to-r from-success to-success-dark hover:shadow-glow"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Execute Rebalancing
                  </Button>
                  
                  <Button
                    id="download-plan-btn"
                    variant="outline"
                    className="glass border-white/20"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download Plan
                  </Button>
                  
                  <Button
                    id="share-optimization-btn"
                    variant="outline"
                    className="glass border-white/20"
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    Share Results
                  </Button>
                </div>
              )}
            </TabsContent>

            {/* Optimization Constraints */}
            <TabsContent value="constraints" className="mt-6">
              <ConstraintsPanel
                constraints={constraints}
                onConstraintsChange={setConstraints}
              />
            </TabsContent>
          </Tabs>

          {/* Analysis Results */}
          {optimizationState.result && (
            <Card id="optimization-analysis" className="glass border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-success" />
                  Optimization Analysis
                </CardTitle>
                <CardDescription>
                  Portfolio insights and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold mb-3 text-success">Strengths</h4>
                    <ul className="space-y-2">
                      {optimizationState.result.analysis.recommendations.map((rec, index) => (
                        <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                          <CheckCircle className="w-3 h-3 text-success mt-0.5 flex-shrink-0" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {optimizationState.result.analysis.warnings.length > 0 && (
                    <div>
                      <h4 className="font-semibold mb-3 text-warning">Considerations</h4>
                      <ul className="space-y-2">
                        {optimizationState.result.analysis.warnings.map((warning, index) => (
                          <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                            <AlertTriangle className="w-3 h-3 text-warning mt-0.5 flex-shrink-0" />
                            {warning}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-white/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Badge variant="outline" className="bg-white/10">
                        Diversification Score: {(optimizationState.result.analysis.diversificationScore * 100).toFixed(0)}%
                      </Badge>
                      <Badge 
                        variant={optimizationState.result.analysis.constraintsSatisfied ? "default" : "destructive"}
                        className={optimizationState.result.analysis.constraintsSatisfied ? "bg-success/20 text-success" : ""}
                      >
                        Constraints: {optimizationState.result.analysis.constraintsSatisfied ? 'Satisfied' : 'Violated'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="pb-20"></div>
      </main>
    </div>
  );
};

export default PortfolioOptimizer;