"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
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
  ExternalLink,
  Monitor,
  Smartphone,
  Tablet
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const features = [
  {
    id: 'monte-carlo',
    icon: BarChart3,
    title: "Monte Carlo Simulations",
    description: "Run thousands of market scenarios to predict your financial future with statistical precision.",
    benefits: [
      "10,000+ scenario simulations",
      "Real-time market data integration",
      "Probability-based outcomes",
      "Risk-adjusted projections"
    ],
    color: "text-blue-600",
    bgColor: "bg-blue-50",
    demoPath: "/demo/interactive?feature=monte-carlo",
    videoPlaceholder: "monte-carlo-demo.mp4"
  },
  {
    id: 'goal-planning',
    icon: Target,
    title: "Goal-Based Planning",
    description: "Set, track, and achieve multiple financial goals with personalized strategies and timelines.",
    benefits: [
      "Multiple goal tracking",
      "Progress visualization",
      "Milestone celebrations",
      "Adaptive strategies"
    ],
    color: "text-green-600",
    bgColor: "bg-green-50",
    demoPath: "/demo/interactive?feature=goals",
    videoPlaceholder: "goal-planning-demo.mp4"
  },
  {
    id: 'risk-analysis',
    icon: Shield,
    title: "Risk Analysis",
    description: "Comprehensive risk assessment with dynamic portfolio optimization and stress testing.",
    benefits: [
      "Multi-factor risk models",
      "Stress testing scenarios",
      "Dynamic rebalancing",
      "Volatility management"
    ],
    color: "text-purple-600",
    bgColor: "bg-purple-50",
    demoPath: "/demo/interactive?feature=risk",
    videoPlaceholder: "risk-analysis-demo.mp4"
  },
  {
    id: 'market-intelligence',
    icon: TrendingUp,
    title: "Market Intelligence",
    description: "Real-time market data with AI-powered insights and predictive analytics.",
    benefits: [
      "Live market feeds",
      "Predictive analytics",
      "Sector analysis",
      "Economic indicators"
    ],
    color: "text-orange-600",
    bgColor: "bg-orange-50",
    demoPath: "/demo/interactive?feature=market",
    videoPlaceholder: "market-intelligence-demo.mp4"
  },
  {
    id: 'social-features',
    icon: Users,
    title: "Social Features",
    description: "Connect with peers, share achievements, and learn from the community.",
    benefits: [
      "Peer comparison",
      "Achievement sharing",
      "Community challenges",
      "Expert mentorship"
    ],
    color: "text-pink-600",
    bgColor: "bg-pink-50",
    demoPath: "/demo/interactive?feature=social",
    videoPlaceholder: "social-features-demo.mp4"
  },
  {
    id: 'ai-recommendations',
    icon: Zap,
    title: "AI Recommendations",
    description: "Machine learning-powered advice tailored to your unique financial situation.",
    benefits: [
      "Personalized insights",
      "Behavioral analysis",
      "Automated rebalancing",
      "Smart notifications"
    ],
    color: "text-yellow-600",
    bgColor: "bg-yellow-50",
    demoPath: "/demo/interactive?feature=ai",
    videoPlaceholder: "ai-recommendations-demo.mp4"
  }
];

const screenshots = {
  desktop: [
    {
      title: "Main Dashboard",
      description: "Comprehensive overview of your financial health",
      placeholder: "dashboard-desktop.png"
    },
    {
      title: "Portfolio Analysis",
      description: "Detailed portfolio breakdown with performance metrics",
      placeholder: "portfolio-desktop.png"
    },
    {
      title: "Goal Tracking",
      description: "Visual progress tracking for all your financial goals",
      placeholder: "goals-desktop.png"
    }
  ],
  tablet: [
    {
      title: "Responsive Design",
      description: "Optimized for tablet viewing and touch interaction",
      placeholder: "dashboard-tablet.png"
    },
    {
      title: "Interactive Charts",
      description: "Touch-friendly charts and visualizations",
      placeholder: "charts-tablet.png"
    }
  ],
  mobile: [
    {
      title: "Mobile Dashboard",
      description: "Full functionality in a mobile-optimized interface",
      placeholder: "dashboard-mobile.png"
    },
    {
      title: "Quick Actions",
      description: "Easy access to key features on mobile devices",
      placeholder: "mobile-actions.png"
    }
  ]
};

export default function FeatureShowcase() {
  const [selectedFeature, setSelectedFeature] = useState(features[0]);
  const [deviceType, setDeviceType] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');

  return (
    <div id="feature-showcase" className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Navigation */}
      <nav id="showcase-nav" className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
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
                  Feature Showcase
                </h1>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/demo/interactive">
                <Button size="sm">
                  Try Interactive Demo
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="showcase-hero" className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="space-y-6"
          >
            <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white">
              Comprehensive Feature
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                {" "}Showcase
              </span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Explore every aspect of our AI Financial Planner. From advanced simulations 
              to intelligent recommendations, discover how each feature works together 
              to optimize your financial future.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features-detailed" className="py-16 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Feature List */}
            <div className="space-y-6">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-8">
                Core Features
              </h2>
              {features.map((feature, index) => {
                const Icon = feature.icon;
                const isSelected = selectedFeature.id === feature.id;
                
                return (
                  <motion.div
                    key={feature.id}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <Card 
                      className={`cursor-pointer transition-all duration-300 hover:shadow-lg ${
                        isSelected ? 'ring-2 ring-blue-500 shadow-lg' : ''
                      }`}
                      onClick={() => setSelectedFeature(feature)}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 ${feature.bgColor} rounded-lg flex items-center justify-center`}>
                            <Icon className={`w-6 h-6 ${feature.color}`} />
                          </div>
                          <div className="flex-1">
                            <CardTitle className="text-lg">{feature.title}</CardTitle>
                          </div>
                          <div className="flex space-x-2">
                            <Link href={feature.demoPath}>
                              <Button size="sm" variant="outline">
                                <Play className="w-4 h-4 mr-1" />
                                Try
                              </Button>
                            </Link>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <CardDescription className="text-base mb-4">
                          {feature.description}
                        </CardDescription>
                        <div className="grid grid-cols-2 gap-2">
                          {feature.benefits.map((benefit, idx) => (
                            <div key={idx} className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                              <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2" />
                              {benefit}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
            </div>

            {/* Feature Detail */}
            <div className="space-y-6">
              <motion.div
                key={selectedFeature.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                <div className="flex items-center space-x-4">
                  <div className={`w-16 h-16 ${selectedFeature.bgColor} rounded-xl flex items-center justify-center`}>
                    <selectedFeature.icon className={`w-8 h-8 ${selectedFeature.color}`} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                      {selectedFeature.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Interactive Feature Demo
                    </p>
                  </div>
                </div>

                {/* Video Placeholder */}
                <div className="relative bg-gray-900 rounded-xl overflow-hidden aspect-video">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center space-y-4">
                      <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto">
                        <Play className="w-8 h-8 text-white ml-1" />
                      </div>
                      <div className="text-white space-y-2">
                        <p className="font-medium">{selectedFeature.title} Demo</p>
                        <p className="text-sm text-gray-300">
                          Video placeholder: {selectedFeature.videoPlaceholder}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="absolute bottom-4 left-4">
                    <Badge className="bg-red-600 text-white">
                      ● Live Demo
                    </Badge>
                  </div>
                </div>

                {/* Feature Benefits */}
                <div className="grid grid-cols-2 gap-4">
                  {selectedFeature.benefits.map((benefit, idx) => (
                    <div key={idx} className="bg-gray-50 dark:bg-slate-800 rounded-lg p-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {benefit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex space-x-4">
                  <Link href={selectedFeature.demoPath} className="flex-1">
                    <Button size="lg" className="w-full">
                      <Play className="w-5 h-5 mr-2" />
                      Try This Feature
                    </Button>
                  </Link>
                  <Button variant="outline" size="lg">
                    <ExternalLink className="w-5 h-5 mr-2" />
                    Learn More
                  </Button>
                </div>
              </motion.div>
            </div>
          </div>
        </div>
      </section>

      {/* Screenshots Section */}
      <section id="screenshots-section" className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Responsive Design
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              Beautiful, functional interface across all devices
            </p>
          </div>

          <Tabs value={deviceType} onValueChange={(value) => setDeviceType(value as any)} className="w-full">
            <TabsList className="grid w-full grid-cols-3 max-w-md mx-auto mb-8">
              <TabsTrigger value="desktop" className="flex items-center space-x-2">
                <Monitor className="w-4 h-4" />
                <span>Desktop</span>
              </TabsTrigger>
              <TabsTrigger value="tablet" className="flex items-center space-x-2">
                <Tablet className="w-4 h-4" />
                <span>Tablet</span>
              </TabsTrigger>
              <TabsTrigger value="mobile" className="flex items-center space-x-2">
                <Smartphone className="w-4 h-4" />
                <span>Mobile</span>
              </TabsTrigger>
            </TabsList>

            {Object.entries(screenshots).map(([device, items]) => (
              <TabsContent key={device} value={device}>
                <div className={`grid gap-8 ${
                  device === 'desktop' ? 'grid-cols-1 lg:grid-cols-3' : 
                  device === 'tablet' ? 'grid-cols-1 md:grid-cols-2' : 
                  'grid-cols-1 sm:grid-cols-2'
                }`}>
                  {items.map((screenshot, index) => (
                    <motion.div
                      key={screenshot.title}
                      initial={{ opacity: 0, y: 20 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.6, delay: index * 0.1 }}
                      viewport={{ once: true }}
                    >
                      <Card className="overflow-hidden">
                        <div className={`bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 flex items-center justify-center ${
                          device === 'desktop' ? 'aspect-video' :
                          device === 'tablet' ? 'aspect-[4/3]' :
                          'aspect-[9/16]'
                        }`}>
                          <div className="text-center space-y-2">
                            <div className={`mx-auto bg-white/20 rounded-lg flex items-center justify-center ${
                              device === 'desktop' ? 'w-16 h-12' :
                              device === 'tablet' ? 'w-12 h-9' :
                              'w-8 h-12'
                            }`}>
                              {device === 'desktop' && <Monitor className="w-8 h-8 text-gray-600" />}
                              {device === 'tablet' && <Tablet className="w-6 h-6 text-gray-600" />}
                              {device === 'mobile' && <Smartphone className="w-4 h-4 text-gray-600" />}
                            </div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {screenshot.placeholder}
                            </p>
                          </div>
                        </div>
                        <CardHeader>
                          <CardTitle className="text-lg">{screenshot.title}</CardTitle>
                          <CardDescription>{screenshot.description}</CardDescription>
                        </CardHeader>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </section>

      {/* CTA Section */}
      <section id="showcase-cta" className="py-20 bg-gradient-to-br from-blue-600 to-purple-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="space-y-8"
          >
            <h2 className="text-3xl lg:text-4xl font-bold text-white">
              Experience the Full Power
            </h2>
            <p className="text-xl text-blue-100 max-w-2xl mx-auto">
              Ready to see these features in action? Try our interactive demo 
              with real sample data and explore every capability.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/demo/interactive">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                  <Play className="w-5 h-5 mr-2" />
                  Start Interactive Demo
                </Button>
              </Link>
              <Link href="/">
                <Button size="lg" variant="outline" className="w-full sm:w-auto border-white text-white hover:bg-white hover:text-blue-600">
                  Try Live App
                  <ExternalLink className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}