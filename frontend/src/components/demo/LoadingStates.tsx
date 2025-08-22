"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, BarChart3, TrendingUp, Target } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function ChartLoadingSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Skeleton className="h-5 w-5" />
          <Skeleton className="h-6 w-32" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Skeleton className="h-64 w-full" />
          <div className="grid grid-cols-3 gap-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DashboardLoadingSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex justify-between items-center">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-40" />
        </div>
        <div className="flex space-x-2">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-40" />
        </div>
      </div>
      
      {/* Cards grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-10 w-10" />
                </div>
                <div className="space-y-2">
                  <Skeleton className="h-8 w-24" />
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {/* Chart skeletons */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartLoadingSkeleton />
        </div>
        <div className="lg:col-span-1">
          <ChartLoadingSkeleton />
        </div>
      </div>
    </div>
  );
}

export function SimulationProgress({ progress, currentStep }: { progress: number; currentStep: string }) {
  const steps = [
    { icon: BarChart3, label: "Analyzing Profile", color: "text-blue-600" },
    { icon: TrendingUp, label: "Running Simulations", color: "text-green-600" },
    { icon: Target, label: "Calculating Goals", color: "text-purple-600" },
    { icon: Loader2, label: "Generating Insights", color: "text-orange-600" }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 bg-white/95 dark:bg-slate-900/95 backdrop-blur-sm z-50 flex items-center justify-center"
    >
      <div className="text-center space-y-8 max-w-md mx-auto px-6">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center"
        >
          <BarChart3 className="w-10 h-10 text-white" />
        </motion.div>
        
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Running Financial Analysis
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {currentStep}
          </p>
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        
        <div className="grid grid-cols-4 gap-4">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = index <= Math.floor(progress / 25);
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: isActive ? 1 : 0.3, y: 0 }}
                transition={{ delay: index * 0.2 }}
                className="text-center"
              >
                <div className={`w-12 h-12 mx-auto rounded-full flex items-center justify-center ${
                  isActive ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-gray-100 dark:bg-gray-800'
                }`}>
                  <Icon className={`w-6 h-6 ${
                    isActive ? step.color : 'text-gray-400'
                  } ${Icon === Loader2 && isActive ? 'animate-spin' : ''}`} />
                </div>
                <p className={`text-xs mt-2 ${
                  isActive ? 'text-gray-900 dark:text-white' : 'text-gray-400'
                }`}>
                  {step.label}
                </p>
              </motion.div>
            );
          })}
        </div>
        
        <p className="text-sm text-gray-500 dark:text-gray-400">
          This typically takes 30-60 seconds
        </p>
      </div>
    </motion.div>
  );
}

export function FeatureHighlight({ title, description, position = 'bottom' }: {
  title: string;
  description: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
}) {
  const positionClasses = {
    top: 'bottom-full mb-2',
    bottom: 'top-full mt-2',
    left: 'right-full mr-2',
    right: 'left-full ml-2'
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className={`absolute z-50 ${positionClasses[position]}`}
    >
      <div className="bg-gray-900 text-white p-4 rounded-lg shadow-xl max-w-sm">
        <div className="space-y-2">
          <h3 className="font-semibold text-sm">{title}</h3>
          <p className="text-xs text-gray-300">{description}</p>
        </div>
        
        {/* Arrow */}
        <div className={`absolute w-2 h-2 bg-gray-900 transform rotate-45 ${
          position === 'top' ? 'top-full left-1/2 -translate-x-1/2 -translate-y-1/2' :
          position === 'bottom' ? 'bottom-full left-1/2 -translate-x-1/2 translate-y-1/2' :
          position === 'left' ? 'left-full top-1/2 -translate-y-1/2 -translate-x-1/2' :
          'right-full top-1/2 -translate-y-1/2 translate-x-1/2'
        }`} />
      </div>
    </motion.div>
  );
}

export function PulsingDot({ className = "" }: { className?: string }) {
  return (
    <div className={`relative ${className}`}>
      <div className="w-3 h-3 bg-blue-500 rounded-full" />
      <div className="absolute inset-0 w-3 h-3 bg-blue-500 rounded-full animate-ping opacity-75" />
    </div>
  );
}

export function FloatingActionButton({ 
  icon: Icon, 
  label, 
  onClick, 
  position = 'bottom-right' 
}: {
  icon: React.ComponentType<any>;
  label: string;
  onClick: () => void;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
}) {
  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6'
  };

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      className={`fixed ${positionClasses[position]} z-40 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg group`}
      onClick={onClick}
    >
      <Icon className="w-6 h-6" />
      <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-3 py-1 rounded text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
        {label}
      </div>
    </motion.button>
  );
}