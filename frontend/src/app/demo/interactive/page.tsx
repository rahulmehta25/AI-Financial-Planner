"use client";

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Target,
  Shield,
  TrendingUp,
  Users,
  Zap,
  Play,
  Pause,
  RotateCcw,
  Lightbulb,
  X,
  ChevronDown,
  Award,
  Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarContent, AvatarFallback } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DemoProfileType, getDemoDataForProfile, demoTradeOffScenarios } from '@/lib/demoData';
import ResultsDashboard from '@/components/ResultsDashboard';\nimport { DemoVisualizations } from '@/components/demo/DemoVisualizations';\nimport { DemoFeatures } from '@/components/demo/DemoFeatures';
import { useFinancialPlanningStore } from '@/store';

interface TourStep {
  id: string;
  target: string;
  title: string;
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right';
}

const tourSteps: TourStep[] = [
  {
    id: 'profile-selector',
    target: '#profile-selector',
    title: 'Choose Your Profile',
    content: 'Start by selecting a demo profile that matches your situation. Each profile has different goals, risk tolerance, and financial circumstances.',
    position: 'bottom'
  },
  {
    id: 'dashboard-overview',
    target: '#demo-dashboard',
    title: 'Financial Dashboard',
    content: 'This is your comprehensive financial overview. See your goals, portfolio performance, and AI-powered insights all in one place.',
    position: 'top'
  },
  {
    id: 'goals-section',
    target: '#goals-section',
    title: 'Goal Tracking',
    content: 'Track progress toward your financial goals with visual indicators and projected completion dates.',
    position: 'left'
  },
  {
    id: 'portfolio-chart',
    target: '#portfolio-chart',
    title: 'Portfolio Analysis',
    content: 'View your asset allocation and see how Monte Carlo simulations predict your portfolio\'s future performance.',
    position: 'top'
  },
  {
    id: 'recommendations',
    target: '#recommendations-panel',
    title: 'AI Recommendations',
    content: 'Get personalized advice based on your financial situation, market conditions, and goal progress.',
    position: 'left'
  },
  {
    id: 'scenarios',
    target: '#trade-off-scenarios',
    title: 'What-If Scenarios',
    content: 'Explore different strategies and see how changes to your plan might affect your outcomes.',
    position: 'top'
  }
];

export default function InteractiveDemo() {
  const [selectedProfile, setSelectedProfile] = useState<DemoProfileType>('young_professional');
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTourStep, setCurrentTourStep] = useState<number | null>(null);
  const [showTooltips, setShowTooltips] = useState(true);
  const [simulationStep, setSimulationStep] = useState(0);
  
  const demoData = getDemoDataForProfile(selectedProfile);
  const { setSimulationResult } = useFinancialPlanningStore();

  useEffect(() => {
    // Set the simulation result for the demo
    setSimulationResult(demoData.simulation);
  }, [selectedProfile, demoData.simulation, setSimulationResult]);

  const startTour = () => {
    setCurrentTourStep(0);
    setShowTooltips(true);
  };

  const nextTourStep = () => {
    if (currentTourStep !== null && currentTourStep < tourSteps.length - 1) {
      setCurrentTourStep(currentTourStep + 1);
    } else {
      setCurrentTourStep(null);
    }
  };

  const closeTour = () => {
    setCurrentTourStep(null);
  };

  const simulateLoading = async () => {
    setIsPlaying(true);
    setSimulationStep(0);
    
    const steps = [
      'Analyzing your financial profile...',
      'Running Monte Carlo simulations...',
      'Calculating goal probabilities...',
      'Generating AI recommendations...',
      'Preparing your dashboard...'
    ];
    
    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSimulationStep(i + 1);
    }
    
    setIsPlaying(false);
  };

  const TourOverlay = () => {
    if (currentTourStep === null) return null;
    
    const step = tourSteps[currentTourStep];
    
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-md mx-4 shadow-xl"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {step.title}
            </h3>
            <Button variant="ghost" size="sm" onClick={closeTour}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            {step.content}
          </p>
          
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              Step {currentTourStep + 1} of {tourSteps.length}
            </span>
            <div className="flex space-x-2">
              {currentTourStep > 0 && (
                <Button variant="outline" size="sm" onClick={() => setCurrentTourStep(currentTourStep - 1)}>
                  Previous
                </Button>
              )}
              <Button size="sm" onClick={nextTourStep}>
                {currentTourStep < tourSteps.length - 1 ? 'Next' : 'Finish'}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    );
  };

  const LoadingSimulation = () => {
    if (!isPlaying) return null;
    
    const steps = [
      'Analyzing your financial profile...',
      'Running Monte Carlo simulations...',
      'Calculating goal probabilities...',
      'Generating AI recommendations...',
      'Preparing your dashboard...'
    ];
    
    return (
      <div className="fixed inset-0 bg-white/90 dark:bg-slate-900/90 z-40 flex items-center justify-center backdrop-blur-sm">
        <div className="text-center space-y-6 max-w-md">
          <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto">
            <BarChart3 className="w-8 h-8 text-blue-600 animate-pulse" />
          </div>
          
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              Running Demo Simulation
            </h3>
            
            <div className="space-y-3">
              {steps.map((step, index) => (
                <div key={index} className="flex items-center justify-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    index < simulationStep ? 'bg-green-500' :
                    index === simulationStep ? 'bg-blue-500 animate-pulse' :
                    'bg-gray-300'
                  }`} />
                  <span className={`text-sm ${
                    index <= simulationStep ? 'text-gray-900 dark:text-white' : 'text-gray-400'
                  }`}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
            
            <Progress value={(simulationStep / steps.length) * 100} className="w-64" />
          </div>
        </div>
      </div>
    );
  };

  if (isPlaying) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
        <LoadingSimulation />
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div id="interactive-demo" className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
        {/* Navigation */}
        <nav id="demo-nav" className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80 sticky top-0 z-30">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-4">
                <Link href="/demo">
                  <Button variant="ghost" size="sm">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Back to Demo
                  </Button>
                </Link>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-5 h-5 text-white" />
                  </div>
                  <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                    Interactive Demo
                  </h1>
                  <Badge className="bg-green-100 text-green-800">
                    Live
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Profile Selector */}
                <div id="profile-selector" className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Profile:</span>
                  <Select value={selectedProfile} onValueChange={(value) => setSelectedProfile(value as DemoProfileType)}>
                    <SelectTrigger className="w-48">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="young_professional">
                        <div className="flex items-center space-x-2">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="text-xs">AJ</AvatarFallback>
                          </Avatar>
                          <span>Young Professional</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="family_oriented">
                        <div className="flex items-center space-x-2">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="text-xs">SW</AvatarFallback>
                          </Avatar>
                          <span>Family-Oriented</span>
                        </div>
                      </SelectItem>
                      <SelectItem value="pre_retiree">
                        <div className="flex items-center space-x-2">
                          <Avatar className="w-6 h-6">
                            <AvatarFallback className="text-xs">RC</AvatarFallback>
                          </Avatar>
                          <span>Pre-Retiree</span>
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm" onClick={startTour}>
                    <Lightbulb className="w-4 h-4 mr-2" />
                    Take Tour
                  </Button>
                  <Button variant="outline" size="sm" onClick={simulateLoading}>
                    <Play className="w-4 h-4 mr-2" />
                    Run Simulation
                  </Button>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => setShowTooltips(!showTooltips)}
                      >
                        <Eye className={`w-4 h-4 ${showTooltips ? 'text-blue-600' : 'text-gray-400'}`} />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      {showTooltips ? 'Hide' : 'Show'} Tooltips
                    </TooltipContent>
                  </Tooltip>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Profile Header */}
        <section id="profile-header" className="py-8 bg-white dark:bg-slate-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              key={selectedProfile}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="flex items-center space-x-6"
            >
              <Avatar className="w-16 h-16">
                <AvatarFallback className="text-lg font-semibold">
                  {demoData.profile.avatar}
                </AvatarFallback>
              </Avatar>
              
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {demoData.profile.name}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {demoData.profile.occupation} • Age {demoData.profile.age}
                </p>
                <div className="flex items-center space-x-6 mt-2">
                  <div className="text-sm">
                    <span className="text-gray-500">Annual Income:</span>
                    <span className="font-medium text-gray-900 dark:text-white ml-1">
                      ${demoData.profile.annualIncome.toLocaleString()}
                    </span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-500">Current Savings:</span>
                    <span className="font-medium text-gray-900 dark:text-white ml-1">
                      ${demoData.profile.currentSavings.toLocaleString()}
                    </span>
                  </div>
                  <Badge variant="outline">
                    {demoData.profile.riskTolerance.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())} Risk
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-sm text-gray-500">Portfolio Value</div>
                  <div className="text-xl font-bold text-green-600">
                    ${demoData.profile.currentSavings.toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">This Month</div>
                  <div className="text-lg font-semibold text-blue-600">
                    +${(demoData.profile.currentSavings * 0.008).toFixed(0)}
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Demo Visualizations */}
        <section id="demo-visualizations" className="py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Interactive Visualizations
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Explore your financial data through dynamic charts and analytics
              </p>
            </div>
            <DemoVisualizations profile={selectedProfile} data={demoData} />
          </div>
        </section>

        {/* Demo Features */}
        <section id="demo-features" className="py-8 bg-white dark:bg-slate-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Advanced Features
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Discover AI-powered insights, gamification, and social features
              </p>
            </div>
            <DemoFeatures data={demoData} onFeatureClick={(feature) => console.log('Feature clicked:', feature)} />
          </div>
        </section>

        {/* Main Demo Dashboard */}
        <div id="demo-dashboard">
          <ResultsDashboard
            result={demoData.simulation}
            onExportPDF={() => {}}
            onRunNewSimulation={() => {}}
            onApplyScenario={() => {}}
            isDemo={true}
            demoProfile={selectedProfile}
          />
        </div>

        {/* Tour Overlay */}
        <TourOverlay />
        
        {/* Demo Footer */}
        <footer id="demo-footer" className="bg-slate-900 text-white py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium">Interactive Demo Complete</p>
                  <p className="text-sm text-gray-400">
                    Ready to start planning your actual financial future?
                  </p>
                </div>
              </div>
              
              <div className="flex space-x-4">
                <Link href="/demo">
                  <Button variant="outline" className="border-gray-600 text-gray-300 hover:bg-gray-800">
                    Back to Overview
                  </Button>
                </Link>
                <Link href="/">
                  <Button className="bg-blue-600 hover:bg-blue-700">
                    Start Your Plan
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </TooltipProvider>
  );
}