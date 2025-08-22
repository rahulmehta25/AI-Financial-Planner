"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  ArrowRight, 
  BarChart3, 
  Shield, 
  Target, 
  TrendingUp, 
  Users, 
  Zap,
  ChevronRight,
  Play,
  Star
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const features = [
  {
    icon: BarChart3,
    title: "Monte Carlo Simulations",
    description: "Run 10,000+ scenarios to predict your financial future with statistical precision",
    color: "text-blue-600",
    bgColor: "bg-blue-50"
  },
  {
    icon: Target,
    title: "Goal-Based Planning",
    description: "Set and track multiple financial goals with personalized strategies",
    color: "text-green-600",
    bgColor: "bg-green-50"
  },
  {
    icon: Shield,
    title: "Risk Analysis",
    description: "Comprehensive risk assessment with dynamic portfolio optimization",
    color: "text-purple-600",
    bgColor: "bg-purple-50"
  },
  {
    icon: TrendingUp,
    title: "Market Intelligence",
    description: "Real-time market data integration with AI-powered insights",
    color: "text-orange-600",
    bgColor: "bg-orange-50"
  },
  {
    icon: Users,
    title: "Social Features",
    description: "Connect with peers, share goals, and learn from the community",
    color: "text-pink-600",
    bgColor: "bg-pink-50"
  },
  {
    icon: Zap,
    title: "AI Recommendations",
    description: "Machine learning-powered advice tailored to your unique situation",
    color: "text-yellow-600",
    bgColor: "bg-yellow-50"
  }
];

const stats = [
  { label: "Success Rate", value: "94%", description: "of users reach their goals" },
  { label: "Average Return", value: "12.4%", description: "annual portfolio growth" },
  { label: "Users Served", value: "50K+", description: "trusted financial plans" },
  { label: "Scenarios Run", value: "10M+", description: "Monte Carlo simulations" }
];

export default function DemoLandingPage() {
  return (
    <div id="demo-landing-page" className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      {/* Navigation */}
      <nav id="demo-nav" className="border-b bg-white/80 backdrop-blur-sm dark:bg-slate-900/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                AI Financial Planner
              </h1>
              <Badge variant="secondary" className="text-xs">
                Demo
              </Badge>
            </div>
            <div className="flex items-center space-x-4">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  Live App
                </Button>
              </Link>
              <Link href="/demo/showcase">
                <Button variant="outline" size="sm">
                  Features
                </Button>
              </Link>
              <Link href="/demo/interactive">
                <Button size="sm">
                  Try Demo
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section id="hero-section" className="py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-8"
            >
              <div className="space-y-4">
                <Badge className="bg-blue-100 text-blue-800 border-blue-200">
                  🚀 Advanced Financial Planning
                </Badge>
                <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 dark:text-white leading-tight">
                  Your Financial Future,
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                    {" "}Powered by AI
                  </span>
                </h1>
                <p className="text-xl text-gray-600 dark:text-gray-300 leading-relaxed">
                  Experience the future of financial planning with our AI-driven platform. 
                  Run Monte Carlo simulations, optimize your portfolio, and achieve your goals 
                  with confidence.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link href="/demo/interactive">
                  <Button size="lg" className="w-full sm:w-auto">
                    <Play className="w-5 h-5 mr-2" />
                    Start Interactive Demo
                  </Button>
                </Link>
                <Link href="/demo/showcase">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    View Features
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 pt-8">
                {stats.map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 + index * 0.1 }}
                    className="text-center"
                  >
                    <div className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
                      {stat.value}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {stat.description}
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              {/* Dashboard Preview */}
              <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-6 border border-gray-200 dark:border-slate-700">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-2xl" />
                
                {/* Mock Dashboard Content */}
                <div className="relative space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Portfolio Performance
                    </h3>
                    <Badge className="bg-green-100 text-green-800">
                      +12.4%
                    </Badge>
                  </div>
                  
                  {/* Mock Chart */}
                  <div className="h-40 bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg flex items-end justify-center space-x-2 p-4">
                    {[0.3, 0.7, 0.4, 0.8, 0.6, 0.9, 0.5, 0.8].map((height, i) => (
                      <div
                        key={i}
                        className="bg-gradient-to-t from-blue-500 to-purple-500 rounded-sm"
                        style={{ height: `${height * 100}%`, width: '12px' }}
                      />
                    ))}
                  </div>
                  
                  {/* Mock Goals */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Retirement Goal</span>
                      <span className="font-medium text-gray-900 dark:text-white">78% Complete</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                      <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{width: '78%'}} />
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Floating elements */}
              <div className="absolute -top-4 -right-4 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium shadow-lg">
                Live Demo
              </div>
              <div className="absolute -bottom-4 -left-4 bg-blue-500 text-white p-3 rounded-full shadow-lg">
                <Star className="w-5 h-5" />
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features-grid" className="py-20 bg-white dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Powerful Features for Smart Planning
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Discover the comprehensive toolkit that makes our AI Financial Planner 
              the most advanced solution for personal financial management.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Card className="h-full hover:shadow-lg transition-shadow duration-300">
                    <CardHeader>
                      <div className={`w-12 h-12 ${feature.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                        <Icon className={`w-6 h-6 ${feature.color}`} />
                      </div>
                      <CardTitle className="text-xl">{feature.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="text-base leading-relaxed">
                        {feature.description}
                      </CardDescription>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="cta-section" className="py-20 bg-gradient-to-br from-blue-600 to-purple-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="space-y-8"
          >
            <h2 className="text-3xl lg:text-4xl font-bold text-white">
              Ready to Transform Your Financial Future?
            </h2>
            <p className="text-xl text-blue-100 max-w-2xl mx-auto">
              Experience the power of AI-driven financial planning. Start your demo 
              journey today and see how our platform can help you achieve your goals.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/demo/interactive">
                <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                  <Play className="w-5 h-5 mr-2" />
                  Start Interactive Demo
                </Button>
              </Link>
              <Link href="/demo/showcase">
                <Button size="lg" variant="outline" className="w-full sm:w-auto border-white text-white hover:bg-white hover:text-blue-600">
                  Explore Features
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer id="demo-footer" className="bg-slate-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold">AI Financial Planner</span>
              </div>
              <p className="text-gray-400">
                Empowering your financial future with artificial intelligence and 
                advanced analytics.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Demo Navigation</h3>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/demo" className="hover:text-white transition-colors">Overview</Link></li>
                <li><Link href="/demo/showcase" className="hover:text-white transition-colors">Feature Showcase</Link></li>
                <li><Link href="/demo/interactive" className="hover:text-white transition-colors">Interactive Demo</Link></li>
                <li><Link href="/" className="hover:text-white transition-colors">Live Application</Link></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Features</h3>
              <ul className="space-y-2 text-gray-400">
                <li>Monte Carlo Simulations</li>
                <li>Goal-Based Planning</li>
                <li>Risk Analysis</li>
                <li>AI Recommendations</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-slate-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 AI Financial Planner Demo. Built with Next.js and TypeScript.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}