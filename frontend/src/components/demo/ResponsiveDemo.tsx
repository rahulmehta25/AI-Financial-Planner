"use client";

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Smartphone, Tablet, Monitor, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ResponsiveDemoProps {
  children: React.ReactNode;
  showDeviceFrame?: boolean;
}

export function ResponsiveDemo({ children, showDeviceFrame = true }: ResponsiveDemoProps) {
  const [deviceType, setDeviceType] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const [isAutoRotating, setIsAutoRotating] = useState(false);

  useEffect(() => {
    if (isAutoRotating) {
      const interval = setInterval(() => {
        setDeviceType(prev => {
          switch (prev) {
            case 'desktop': return 'tablet';
            case 'tablet': return 'mobile';
            case 'mobile': return 'desktop';
            default: return 'desktop';
          }
        });
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isAutoRotating]);

  const deviceConfigs = {
    mobile: {
      width: 375,
      height: 667,
      className: 'max-w-sm mx-auto',
      frameClass: 'bg-gray-900 rounded-[2rem] p-2',
      screenClass: 'bg-black rounded-[1.5rem] overflow-hidden'
    },
    tablet: {
      width: 768,
      height: 1024,
      className: 'max-w-2xl mx-auto',
      frameClass: 'bg-gray-800 rounded-2xl p-3',
      screenClass: 'bg-gray-900 rounded-xl overflow-hidden'
    },
    desktop: {
      width: 1200,
      height: 800,
      className: 'max-w-6xl mx-auto',
      frameClass: 'bg-gray-700 rounded-lg p-4',
      screenClass: 'bg-white dark:bg-gray-900 rounded overflow-hidden'
    }
  };

  const currentConfig = deviceConfigs[deviceType];

  return (
    <div className="space-y-6">
      {/* Device Controls */}
      <div className="flex items-center justify-center space-x-4">
        <div className="flex items-center space-x-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          {[
            { type: 'desktop' as const, icon: Monitor, label: 'Desktop' },
            { type: 'tablet' as const, icon: Tablet, label: 'Tablet' },
            { type: 'mobile' as const, icon: Smartphone, label: 'Mobile' }
          ].map(({ type, icon: Icon, label }) => (
            <Button
              key={type}
              variant={deviceType === type ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setDeviceType(type)}
              className="flex items-center space-x-2"
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </Button>
          ))}
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsAutoRotating(!isAutoRotating)}
          className={cn(
            "transition-colors",
            isAutoRotating && "bg-blue-50 text-blue-600 border-blue-200"
          )}
        >
          {isAutoRotating ? 'Stop' : 'Auto'} Rotate
        </Button>
      </div>

      {/* Device Preview */}
      <motion.div
        key={deviceType}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className={currentConfig.className}
      >
        {showDeviceFrame ? (
          <div className={currentConfig.frameClass}>
            <div className={currentConfig.screenClass}>
              <div className="h-full overflow-auto">
                {children}
              </div>
            </div>
          </div>
        ) : (
          <div className={`w-full ${currentConfig.screenClass}`}>
            {children}
          </div>
        )}
      </motion.div>

      {/* Device Info */}
      <div className="text-center text-sm text-gray-600 dark:text-gray-400">
        {deviceType.charAt(0).toUpperCase() + deviceType.slice(1)} View
        {deviceType === 'mobile' && ' (375×667px)'}
        {deviceType === 'tablet' && ' (768×1024px)'}
        {deviceType === 'desktop' && ' (1200×800px)'}
      </div>
    </div>
  );
}

export function MobileOptimizedCard({ title, children, className = "" }: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader 
        className="cursor-pointer sm:cursor-default"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{title}</CardTitle>
          <ChevronDown 
            className={cn(
              "w-5 h-5 transition-transform sm:hidden",
              isExpanded && "rotate-180"
            )} 
          />
        </div>
      </CardHeader>
      
      <motion.div
        initial={false}
        animate={{ height: isExpanded ? 'auto' : 0 }}
        className="sm:h-auto overflow-hidden"
      >
        <CardContent className="sm:block">
          {children}
        </CardContent>
      </motion.div>
    </Card>
  );
}

export function ResponsiveGrid({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn(
      "grid gap-4",
      "grid-cols-1", // Mobile: 1 column
      "sm:grid-cols-2", // Small: 2 columns
      "lg:grid-cols-3", // Large: 3 columns
      "xl:grid-cols-4", // Extra large: 4 columns
      className
    )}>
      {children}
    </div>
  );
}

export function ResponsiveNavigation({ items }: {
  items: { label: string; href: string; active?: boolean }[];
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden md:flex space-x-6">
        {items.map((item, index) => (
          <a
            key={index}
            href={item.href}
            className={cn(
              "px-3 py-2 rounded-md text-sm font-medium transition-colors",
              item.active
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100"
                : "text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white"
            )}
          >
            {item.label}
          </a>
        ))}
      </nav>

      {/* Mobile Navigation */}
      <div className="md:hidden">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          Menu
        </Button>
        
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute top-full left-0 right-0 bg-white dark:bg-gray-900 shadow-lg border-t z-50"
          >
            <div className="py-2">
              {items.map((item, index) => (
                <a
                  key={index}
                  href={item.href}
                  className={cn(
                    "block px-4 py-2 text-sm transition-colors",
                    item.active
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-100"
                      : "text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  )}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {item.label}
                </a>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </>
  );
}