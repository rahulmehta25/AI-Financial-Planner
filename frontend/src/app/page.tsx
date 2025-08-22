"use client";

import React, { useState, useEffect } from 'react';
import { FormWizard } from '@/components/forms';
import ResultsDashboard from '@/components/ResultsDashboard';
import { useFinancialPlanningStore } from '@/store';
import { financialPlanningAPI, mockSimulationResult } from '@/lib/api';
import { exportToPDF } from '@/lib/pdfExport';
import { SimulationResult, TradeOffScenario } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, AlertCircle, RotateCcw } from 'lucide-react';

type AppState = 'form' | 'loading' | 'results' | 'error';

export default function HomePage() {
  const [appState, setAppState] = useState<AppState>('form');
  const [error, setError] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  
  const { 
    formData, 
    resetForm, 
    setLoading, 
    addNotification,
    simulationResult: storedResult,
    setSimulationResult: setStoredResult
  } = useFinancialPlanningStore();

  // Load existing result if available
  useEffect(() => {
    if (storedResult && !simulationResult) {
      setSimulationResult(storedResult);
      setAppState('results');
    }
  }, [storedResult, simulationResult]);

  // Listen for form submission events
  useEffect(() => {
    const handleSubmit = (event: CustomEvent) => {
      handleFormSubmit(event.detail);
    };

    window.addEventListener('financialPlanSubmit', handleSubmit as EventListener);
    return () => {
      window.removeEventListener('financialPlanSubmit', handleSubmit as EventListener);
    };
  }, []);

  const handleFormSubmit = async (finalFormData: any) => {
    setAppState('loading');
    setLoading('isSubmitting', true);
    setError(null);

    try {
      // In development, use mock data
      if (process.env.NODE_ENV === 'development') {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        const result: SimulationResult = {
          ...mockSimulationResult,
          id: `sim-${Date.now()}`,
          timestamp: new Date().toISOString(),
        };
        
        setSimulationResult(result);
        setStoredResult(result);
        setAppState('results');
        
        addNotification({
          type: 'success',
          title: 'Analysis Complete',
          message: 'Your financial plan has been generated successfully!',
        });
      } else {
        // Production API call
        const response = await financialPlanningAPI.runSimulation(finalFormData);
        
        if (response.success && response.data) {
          setSimulationResult(response.data);
          setStoredResult(response.data);
          setAppState('results');
          
          addNotification({
            type: 'success',
            title: 'Analysis Complete',
            message: 'Your financial plan has been generated successfully!',
          });
        } else {
          throw new Error(response.error?.message || 'Simulation failed');
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      setAppState('error');
      
      addNotification({
        type: 'error',
        title: 'Analysis Failed',
        message: errorMessage,
      });
    } finally {
      setLoading('isSubmitting', false);
    }
  };

  const handleExportPDF = async () => {
    if (!simulationResult) return;
    
    setLoading('isExportingPDF', true);
    
    try {
      await exportToPDF(simulationResult, formData);
      
      addNotification({
        type: 'success',
        title: 'PDF Exported',
        message: 'Your financial plan has been downloaded successfully!',
      });
    } catch (err) {
      addNotification({
        type: 'error',
        title: 'Export Failed',
        message: 'Failed to generate PDF. Please try again.',
      });
    } finally {
      setLoading('isExportingPDF', false);
    }
  };

  const handleRunNewSimulation = () => {
    setAppState('form');
    setSimulationResult(null);
    setError(null);
    resetForm();
  };

  const handleApplyScenario = async (scenario: TradeOffScenario) => {
    if (!simulationResult) return;
    
    // In a real implementation, this would modify the form data based on the scenario
    // and run a new simulation
    addNotification({
      type: 'info',
      title: 'Scenario Applied',
      message: `Applied scenario: ${scenario.title}. Run a new analysis to see the results.`,
    });
  };

  const handleRetry = () => {
    setAppState('form');
    setError(null);
  };

  const LoadingScreen = () => (
    <div id="loading-screen" className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="max-w-md mx-auto text-center">
        <div className="mb-8">
          <Loader2 className="w-16 h-16 animate-spin text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Analyzing Your Financial Future
          </h2>
          <p className="text-muted-foreground">
            Running Monte Carlo simulation with 10,000 scenarios...
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
          <div className="space-y-4">
            {[
              'Processing your financial data',
              'Running market simulations',
              'Calculating probability scenarios',
              'Generating recommendations',
              'Preparing your personalized plan'
            ].map((step, index) => (
              <div key={index} className="flex items-center text-sm text-left">
                <div className="w-2 h-2 bg-primary rounded-full mr-3 animate-pulse"></div>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
        
        <p className="text-xs text-muted-foreground mt-4">
          This process typically takes 30-60 seconds
        </p>
      </div>
    </div>
  );

  const ErrorScreen = () => (
    <div id="error-screen" className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <Card className="max-w-md mx-auto">
        <CardHeader>
          <div className="flex items-center gap-3">
            <AlertCircle className="w-8 h-8 text-red-500" />
            <div>
              <CardTitle className="text-red-900 dark:text-red-100">
                Analysis Failed
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                We encountered an issue processing your request
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-800 dark:text-red-200">
                {error}
              </p>
            </div>
            
            <div className="flex gap-3">
              <Button
                onClick={handleRetry}
                className="flex-1"
                variant="outline"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
              <Button
                onClick={handleRunNewSimulation}
                className="flex-1"
              >
                Start Over
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Render based on app state
  switch (appState) {
    case 'form':
      return <FormWizard />;
    
    case 'loading':
      return <LoadingScreen />;
    
    case 'error':
      return <ErrorScreen />;
    
    case 'results':
      return simulationResult ? (
        <ResultsDashboard
          result={simulationResult}
          onExportPDF={handleExportPDF}
          onRunNewSimulation={handleRunNewSimulation}
          onApplyScenario={handleApplyScenario}
        />
      ) : null;
    
    default:
      return <FormWizard />;
  }
}