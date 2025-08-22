'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import { 
  Sun, 
  Moon, 
  Download, 
  TrendingUp, 
  Shield, 
  Target, 
  PieChart, 
  Calculator,
  Award,
  Zap,
  ArrowRight,
  ArrowLeft,
  ChevronDown,
  DollarSign,
  Clock,
  BarChart3,
  Sparkles,
  Users,
  Home,
  Briefcase,
  Heart,
  Brain,
  CheckCircle,
  Play,
  Pause,
  Star,
  Trophy,
  Gift,
  Lightbulb,
  Eye,
  EyeOff
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarContent, AvatarFallback } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { getDemoDataForProfile, DemoProfileType, demoTradeOffScenarios } from '@/lib/demoData';

// Enhanced chart components with animations
const AnimatedLineChart = ({ data, className }: { data: any[], className?: string }) => {
  const [animatedData, setAnimatedData] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      if (currentIndex < data.length) {
        setAnimatedData(prev => [...prev, data[currentIndex]]);
        setCurrentIndex(prev => prev + 1);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [data, currentIndex]);

  const maxValue = Math.max(...data.map(d => d.value));

  return (
    <div className={`relative h-40 ${className}`}>
      <svg width="100%" height="100%" className="overflow-visible">
        <defs>
          <linearGradient id="chartGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="rgb(59, 130, 246)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="rgb(59, 130, 246)" stopOpacity="0" />
          </linearGradient>
        </defs>
        
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map(percent => (
          <line
            key={percent}
            x1="0"
            y1={`${percent}%`}
            x2="100%"
            y2={`${percent}%`}
            stroke="currentColor"
            strokeOpacity="0.1"
            strokeWidth="1"
          />
        ))}

        {/* Animated line */}
        {animatedData.length > 1 && (
          <>
            <motion.path
              d={`M ${animatedData.map((d, i) => 
                `${(i / (data.length - 1)) * 100},${100 - (d.value / maxValue) * 100}`
              ).join(' L ')}`}
              fill="url(#chartGradient)"
              stroke="none"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, ease: "easeInOut" }}
            />
            <motion.path
              d={`M ${animatedData.map((d, i) => 
                `${(i / (data.length - 1)) * 100},${100 - (d.value / maxValue) * 100}`
              ).join(' L ')}`}
              fill="none"
              stroke="rgb(59, 130, 246)"
              strokeWidth="2"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 2, ease: "easeInOut" }}
            />
          </>
        )}

        {/* Animated dots */}
        {animatedData.map((d, i) => (
          <motion.circle
            key={i}
            cx={`${(i / (data.length - 1)) * 100}%`}
            cy={`${100 - (d.value / maxValue) * 100}%`}
            r="3"
            fill="rgb(59, 130, 246)"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: i * 0.05 }}
          />
        ))}
      </svg>
    </div>
  );
};

const AnimatedPieChart = ({ data, size = 120 }: { data: any[], size?: number }) => {
  const [animatedSegments, setAnimatedSegments] = useState<any[]>([]);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedSegments(data);
    }, 500);
    return () => clearTimeout(timer);
  }, [data]);

  const total = data.reduce((sum, item) => sum + item.value, 0);
  let cumulativeAngle = 0;
  const radius = size / 2 - 10;
  const centerX = size / 2;
  const centerY = size / 2;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        {animatedSegments.map((item, index) => {
          const startAngle = cumulativeAngle;
          const sweepAngle = (item.value / total) * 360;
          cumulativeAngle += sweepAngle;

          const startAngleRad = (startAngle * Math.PI) / 180;
          const endAngleRad = ((startAngle + sweepAngle) * Math.PI) / 180;

          const largeArcFlag = sweepAngle > 180 ? 1 : 0;

          const x1 = centerX + radius * Math.cos(startAngleRad);
          const y1 = centerY + radius * Math.sin(startAngleRad);
          const x2 = centerX + radius * Math.cos(endAngleRad);
          const y2 = centerY + radius * Math.sin(endAngleRad);

          const pathData = [
            `M ${centerX} ${centerY}`,
            `L ${x1} ${y1}`,
            `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
            'Z'
          ].join(' ');

          return (
            <motion.path
              key={index}
              d={pathData}
              fill={item.color}
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ delay: index * 0.2, duration: 0.8, ease: "easeOut" }}
            />
          );
        })}
      </svg>
    </div>
  );
};

// Profile selection component
const ProfileSelector = ({ selectedProfile, onProfileChange }: { 
  selectedProfile: DemoProfileType, 
  onProfileChange: (profile: DemoProfileType) => void 
}) => {
  const profiles = [
    { key: 'young_professional' as DemoProfileType, icon: Briefcase, title: 'Young Professional', desc: 'Starting career, building wealth' },
    { key: 'family_oriented' as DemoProfileType, icon: Heart, title: 'Family Focused', desc: 'Managing family finances' },
    { key: 'pre_retiree' as DemoProfileType, icon: Home, title: 'Pre-Retiree', desc: 'Preparing for retirement' }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {profiles.map(({ key, icon: Icon, title, desc }) => (
        <motion.div
          key={key}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Card 
            className={`cursor-pointer transition-all duration-300 ${
              selectedProfile === key 
                ? 'ring-2 ring-blue-500 shadow-lg bg-blue-50 dark:bg-blue-950' 
                : 'hover:shadow-md'
            }`}
            onClick={() => onProfileChange(key)}
          >
            <CardContent className="p-6 text-center">
              <Icon className={`mx-auto mb-3 h-8 w-8 ${selectedProfile === key ? 'text-blue-600' : 'text-gray-600'}`} />
              <h3 className="font-semibold mb-1">{title}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">{desc}</p>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
};

// Animated number counter
const AnimatedNumber = ({ value, prefix = '', suffix = '', duration = 2000 }: {
  value: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref);

  useEffect(() => {
    if (isInView) {
      let startTime: number;
      const animate = (currentTime: number) => {
        if (!startTime) startTime = currentTime;
        const progress = Math.min((currentTime - startTime) / duration, 1);
        
        const easeOut = 1 - Math.pow(1 - progress, 3);
        setDisplayValue(Math.floor(value * easeOut));
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };
      requestAnimationFrame(animate);
    }
  }, [isInView, value, duration]);

  return (
    <span ref={ref}>
      {prefix}{displayValue.toLocaleString()}{suffix}
    </span>
  );
};

// Main demo page component
export default function CompleteDemoPage() {
  const [darkMode, setDarkMode] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<DemoProfileType>('young_professional');
  const [currentSection, setCurrentSection] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [formData, setFormData] = useState({
    monthlyIncome: 7500,
    monthlyExpenses: 4200,
    currentSavings: 45000,
    riskTolerance: 'moderate'
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const demoData = getDemoDataForProfile(selectedProfile);
  
  // Auto-play functionality
  useEffect(() => {
    if (isAutoPlaying) {
      const interval = setInterval(() => {
        setCurrentSection(prev => (prev + 1) % 8);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isAutoPlaying]);

  // Theme effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const sections = [
    'profile',
    'onboarding', 
    'financial-form',
    'simulation',
    'portfolio',
    'goals',
    'risk',
    'achievements'
  ];

  const scrollToSection = (index: number) => {
    setCurrentSection(index);
    const element = document.getElementById(sections[index]);
    element?.scrollIntoView({ behavior: 'smooth' });
  };

  // Export to PDF functionality
  const exportToPDF = async () => {
    // Mock PDF generation with loading state
    const button = document.getElementById('export-btn') as HTMLButtonElement;
    if (button) {
      button.disabled = true;
      button.textContent = 'Generating PDF...';
      
      // Simulate PDF generation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Create and download a mock PDF
      const element = document.createElement('a');
      element.href = 'data:application/pdf;base64,JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVGl0bGUgKEZpbmFuY2lhbCBQbGFubmluZyBSZXBvcnQpCi9Qcm9kdWNlciAoRmluYW5jaWFsIFBsYW5uZXIgRGVtbykKL0NyZWF0aW9uRGF0ZSAoRDoyMDI0MDgyMjAwMDAwMFopCj4+CmVuZG9iagp4cmVmCjAgMQowMDAwMDAwMDAwIDY1NTM1IGYgCnRyYWlsZXIKPDwKL1NpemUgMQovUm9vdCAxIDAgUgo+PgpzdGFydHhyZWYKMTczCiUlRU9G';
      element.download = `Financial_Plan_${selectedProfile}_${new Date().toISOString().split('T')[0]}.pdf`;
      element.click();
      
      button.disabled = false;
      button.textContent = 'Download PDF Report';
    }
  };

  const heroSection = (
    <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900 dark:to-purple-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0">
        {[...Array(20)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-blue-400 rounded-full opacity-20"
            animate={{
              x: [0, Math.random() * 100, 0],
              y: [0, Math.random() * 100, 0],
            }}
            transition={{
              duration: 10 + Math.random() * 10,
              repeat: Infinity,
              ease: "linear"
            }}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
          />
        ))}
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring" }}
            className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full mb-8"
          >
            <TrendingUp className="w-10 h-10 text-white" />
          </motion.div>
          
          <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-6">
            Financial Planning
          </h1>
          <h2 className="text-3xl md:text-4xl font-semibold mb-6 text-gray-800 dark:text-gray-200">
            Complete Demo Experience
          </h2>
          
          <motion.p 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto"
          >
            Experience the full power of AI-driven financial planning with Monte Carlo simulations, 
            portfolio optimization, and personalized recommendations.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12"
          >
            <Button 
              onClick={() => scrollToSection(1)}
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 text-lg"
            >
              Start Demo <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            
            <Button 
              onClick={() => setIsAutoPlaying(!isAutoPlaying)}
              variant="outline"
              size="lg"
              className="px-8 py-3 text-lg"
            >
              {isAutoPlaying ? <Pause className="mr-2 h-5 w-5" /> : <Play className="mr-2 h-5 w-5" />}
              {isAutoPlaying ? 'Pause Tour' : 'Auto Tour'}
            </Button>
          </motion.div>

          {/* Feature highlights */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto"
          >
            {[
              { icon: Calculator, label: 'Monte Carlo Simulations' },
              { icon: PieChart, label: 'Portfolio Optimization' },
              { icon: Target, label: 'Goal Tracking' },
              { icon: Shield, label: 'Risk Assessment' }
            ].map(({ icon: Icon, label }, index) => (
              <motion.div
                key={label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1 + index * 0.1 }}
                className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-lg p-4 text-center"
              >
                <Icon className="h-8 w-8 mx-auto mb-2 text-blue-600" />
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</p>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll indicator */}
      <motion.div
        animate={{ y: [0, 10, 0] }}
        transition={{ repeat: Infinity, duration: 2 }}
        className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
      >
        <ChevronDown className="h-8 w-8 text-gray-400" />
      </motion.div>
    </section>
  );

  return (
    <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark' : ''}`}>
      {/* Fixed header */}
      <motion.header 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="fixed top-0 left-0 right-0 z-50 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700"
      >
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold">Financial Planner</span>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Section navigation */}
            <nav className="hidden md:flex items-center gap-2">
              {sections.map((section, index) => (
                <Button
                  key={section}
                  variant={currentSection === index ? "default" : "ghost"}
                  size="sm"
                  onClick={() => scrollToSection(index)}
                  className="capitalize"
                >
                  {section.replace('-', ' ')}
                </Button>
              ))}
            </nav>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDarkMode(!darkMode)}
              className="p-2"
            >
              {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            
            <Button
              id="export-btn"
              onClick={exportToPDF}
              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
            >
              <Download className="mr-2 h-4 w-4" />
              Download PDF Report
            </Button>
          </div>
        </div>
      </motion.header>

      {heroSection}

      {/* Profile Selection Section */}
      <section id="profile" className="py-20 bg-white dark:bg-gray-900">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Choose Your Profile
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Select a profile that matches your financial situation to see personalized recommendations
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <ProfileSelector 
              selectedProfile={selectedProfile} 
              onProfileChange={setSelectedProfile} 
            />
          </motion.div>

          {/* Profile details */}
          <motion.div
            key={selectedProfile}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="mt-12 max-w-4xl mx-auto"
          >
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarContent className="text-xl font-bold">
                      {demoData.profile.avatar}
                    </AvatarContent>
                    <AvatarFallback>{demoData.profile.avatar}</AvatarFallback>
                  </Avatar>
                  <div>
                    <CardTitle className="text-2xl">{demoData.profile.name}</CardTitle>
                    <p className="text-gray-600 dark:text-gray-400">{demoData.profile.occupation}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Age</p>
                    <p className="text-2xl font-bold">{demoData.profile.age}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Annual Income</p>
                    <p className="text-2xl font-bold">
                      <AnimatedNumber value={demoData.profile.annualIncome} prefix="$" />
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Current Savings</p>
                    <p className="text-2xl font-bold">
                      <AnimatedNumber value={demoData.profile.currentSavings} prefix="$" />
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Risk Tolerance</p>
                    <Badge variant="secondary" className="mt-1">
                      {demoData.profile.riskTolerance.replace('-', ' ')}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* Onboarding Flow Section */}
      <section id="onboarding" className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">User Onboarding Flow</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Interactive step-by-step process to gather financial information
            </p>
          </motion.div>

          <div className="max-w-4xl mx-auto">
            {/* Progress indicator */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mb-12"
            >
              <div className="flex items-center justify-between mb-4">
                {['Personal Info', 'Financial Snapshot', 'Account Buckets', 'Risk Assessment', 'Goals'].map((step, index) => (
                  <div key={step} className="flex items-center">
                    <motion.div
                      initial={{ scale: 0 }}
                      whileInView={{ scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                        index <= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {index + 1}
                    </motion.div>
                    {index < 4 && (
                      <div className={`h-1 w-16 mx-2 ${index < 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
                    )}
                  </div>
                ))}
              </div>
              <Progress value={60} className="h-2" />
            </motion.div>

            {/* Sample onboarding cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { title: 'Quick Start', desc: 'Answer 3 quick questions', time: '2 min', completed: true },
                { title: 'Financial Details', desc: 'Income, expenses, savings', time: '5 min', completed: true },
                { title: 'Goals & Preferences', desc: 'Risk tolerance, goals', time: '3 min', completed: false }
              ].map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className={`${item.completed ? 'bg-green-50 dark:bg-green-950 border-green-200' : ''}`}>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold">{item.title}</h3>
                        {item.completed ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : (
                          <Clock className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{item.desc}</p>
                      <div className="flex items-center justify-between">
                        <Badge variant="outline">{item.time}</Badge>
                        <Button size="sm" variant={item.completed ? "outline" : "default"}>
                          {item.completed ? 'Edit' : 'Continue'}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Financial Profile Form Section */}
      <section id="financial-form" className="py-20 bg-white dark:bg-gray-900">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Interactive Financial Form</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Smart form with real-time validation and recommendations
            </p>
          </motion.div>

          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Financial Information</CardTitle>
                    <Button 
                      variant="outline" 
                      onClick={() => setShowAdvanced(!showAdvanced)}
                    >
                      {showAdvanced ? <EyeOff className="mr-2 h-4 w-4" /> : <Eye className="mr-2 h-4 w-4" />}
                      {showAdvanced ? 'Simple View' : 'Advanced View'}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="income" className="w-full">
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="income">Income</TabsTrigger>
                      <TabsTrigger value="expenses">Expenses</TabsTrigger>
                      <TabsTrigger value="savings">Savings</TabsTrigger>
                      <TabsTrigger value="goals">Goals</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="income" className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium mb-2">Monthly Income</label>
                          <Input
                            type="number"
                            value={formData.monthlyIncome}
                            onChange={(e) => setFormData({...formData, monthlyIncome: Number(e.target.value)})}
                            className="text-lg"
                          />
                          <p className="text-sm text-gray-500 mt-1">
                            Annual: ${(formData.monthlyIncome * 12).toLocaleString()}
                          </p>
                        </div>
                        
                        {showAdvanced && (
                          <div>
                            <label className="block text-sm font-medium mb-2">Income Sources</label>
                            <div className="space-y-2">
                              <div className="flex items-center space-x-2">
                                <Checkbox id="salary" defaultChecked />
                                <label htmlFor="salary" className="text-sm">Salary</label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Checkbox id="bonus" />
                                <label htmlFor="bonus" className="text-sm">Annual Bonus</label>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Checkbox id="freelance" />
                                <label htmlFor="freelance" className="text-sm">Freelance Income</label>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* Real-time income analysis */}
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <Lightbulb className="h-5 w-5 text-blue-600" />
                          <span className="font-medium">AI Insight</span>
                        </div>
                        <p className="text-sm">
                          Your income puts you in the {formData.monthlyIncome > 8000 ? 'upper' : formData.monthlyIncome > 5000 ? 'middle' : 'lower'} income bracket. 
                          Consider maximizing your 401(k) contribution to ${Math.min(formData.monthlyIncome * 0.15, 2000).toLocaleString()}/month.
                        </p>
                      </motion.div>
                    </TabsContent>
                    
                    <TabsContent value="expenses" className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium mb-2">Monthly Expenses</label>
                          <Input
                            type="number"
                            value={formData.monthlyExpenses}
                            onChange={(e) => setFormData({...formData, monthlyExpenses: Number(e.target.value)})}
                            className="text-lg"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium mb-2">Savings Rate</label>
                          <div className="text-2xl font-bold text-green-600">
                            {((formData.monthlyIncome - formData.monthlyExpenses) / formData.monthlyIncome * 100).toFixed(1)}%
                          </div>
                          <Progress 
                            value={(formData.monthlyIncome - formData.monthlyExpenses) / formData.monthlyIncome * 100} 
                            className="mt-2"
                          />
                        </div>
                      </div>
                      
                      {showAdvanced && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {[
                            { label: 'Housing', value: Math.round(formData.monthlyExpenses * 0.3) },
                            { label: 'Food', value: Math.round(formData.monthlyExpenses * 0.15) },
                            { label: 'Transport', value: Math.round(formData.monthlyExpenses * 0.15) },
                            { label: 'Other', value: Math.round(formData.monthlyExpenses * 0.4) }
                          ].map(({ label, value }) => (
                            <div key={label} className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded">
                              <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
                              <p className="text-lg font-semibold">${value}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </TabsContent>
                    
                    <TabsContent value="savings" className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium mb-2">Current Savings</label>
                          <Input
                            type="number"
                            value={formData.currentSavings}
                            onChange={(e) => setFormData({...formData, currentSavings: Number(e.target.value)})}
                            className="text-lg"
                          />
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium mb-2">Emergency Fund Status</label>
                          <div className="space-y-2">
                            <div className="flex justify-between">
                              <span>Months Covered</span>
                              <span className="font-semibold">
                                {(formData.currentSavings / formData.monthlyExpenses).toFixed(1)} months
                              </span>
                            </div>
                            <Progress 
                              value={Math.min((formData.currentSavings / formData.monthlyExpenses) / 6 * 100, 100)} 
                            />
                            <p className="text-sm text-gray-500">Target: 6 months of expenses</p>
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                    
                    <TabsContent value="goals" className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium mb-2">Risk Tolerance</label>
                          <Select 
                            value={formData.riskTolerance} 
                            onValueChange={(value) => setFormData({...formData, riskTolerance: value})}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="conservative">Conservative</SelectItem>
                              <SelectItem value="moderate">Moderate</SelectItem>
                              <SelectItem value="aggressive">Aggressive</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium mb-2">Primary Goal</label>
                          <Select defaultValue="retirement">
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="retirement">Retirement</SelectItem>
                              <SelectItem value="house">House Down Payment</SelectItem>
                              <SelectItem value="education">Education Fund</SelectItem>
                              <SelectItem value="emergency">Emergency Fund</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Monte Carlo Simulation Results */}
      <section id="simulation" className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Monte Carlo Simulation Results</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              AI-powered analysis of 10,000 market scenarios
            </p>
          </motion.div>

          <div className="max-w-6xl mx-auto space-y-8">
            {/* Key metrics */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-6"
            >
              {[
                { 
                  title: 'Success Probability', 
                  value: demoData.simulation.scenarios.realistic.goalAchievementRate, 
                  suffix: '%',
                  color: 'text-green-600',
                  icon: Target 
                },
                { 
                  title: 'Expected Growth', 
                  value: demoData.simulation.scenarios.realistic.projectedGrowth, 
                  suffix: '%',
                  color: 'text-blue-600',
                  icon: TrendingUp 
                },
                { 
                  title: 'Risk Score', 
                  value: demoData.simulation.riskMetrics.volatility, 
                  suffix: '%',
                  color: 'text-orange-600',
                  icon: Shield 
                }
              ].map(({ title, value, suffix, color, icon: Icon }) => (
                <Card key={title} className="text-center">
                  <CardContent className="p-6">
                    <Icon className={`h-8 w-8 mx-auto mb-3 ${color}`} />
                    <h3 className="font-semibold mb-2">{title}</h3>
                    <div className={`text-3xl font-bold ${color}`}>
                      <AnimatedNumber value={value} suffix={suffix} />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </motion.div>

            {/* Scenario comparison */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Scenario Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                      { scenario: 'Optimistic', data: demoData.simulation.scenarios.optimistic, color: 'green' },
                      { scenario: 'Realistic', data: demoData.simulation.scenarios.realistic, color: 'blue' },
                      { scenario: 'Pessimistic', data: demoData.simulation.scenarios.pessimistic, color: 'red' }
                    ].map(({ scenario, data, color }) => (
                      <div key={scenario} className="text-center">
                        <h4 className="font-semibold mb-4">{scenario} Scenario</h4>
                        <div className="space-y-3">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Final Value</p>
                            <p className={`text-xl font-bold text-${color}-600`}>
                              <AnimatedNumber value={data.finalValue} prefix="$" />
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Success Rate</p>
                            <p className={`text-lg font-semibold text-${color}-600`}>
                              {data.goalAchievementRate}%
                            </p>
                          </div>
                          <Progress 
                            value={data.goalAchievementRate} 
                            className={`h-2 bg-${color}-100`}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Portfolio projection chart */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Portfolio Value Projection</CardTitle>
                </CardHeader>
                <CardContent>
                  <AnimatedLineChart 
                    data={demoData.simulation.monthlyProjections.map(p => ({ value: p.portfolioValue }))}
                    className="w-full"
                  />
                  <div className="grid grid-cols-3 gap-4 mt-6 text-center">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Current Value</p>
                      <p className="text-lg font-semibold">
                        <AnimatedNumber value={demoData.simulation.monthlyProjections[0].portfolioValue} prefix="$" />
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">1 Year Projection</p>
                      <p className="text-lg font-semibold">
                        <AnimatedNumber 
                          value={demoData.simulation.monthlyProjections[demoData.simulation.monthlyProjections.length - 1].portfolioValue} 
                          prefix="$" 
                        />
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Total Growth</p>
                      <p className="text-lg font-semibold text-green-600">
                        +<AnimatedNumber 
                          value={demoData.simulation.monthlyProjections[demoData.simulation.monthlyProjections.length - 1].portfolioValue - demoData.simulation.monthlyProjections[0].portfolioValue} 
                          prefix="$" 
                        />
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Portfolio Recommendations */}
      <section id="portfolio" className="py-20 bg-white dark:bg-gray-900">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Portfolio Recommendations</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              AI-optimized allocation based on your risk profile and goals
            </p>
          </motion.div>

          <div className="max-w-6xl mx-auto space-y-8">
            {/* Portfolio allocation visualization */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <PieChart className="h-5 w-5" />
                    Recommended Portfolio Allocation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="flex justify-center">
                      <AnimatedPieChart
                        data={[
                          { value: demoData.portfolio.stocks, color: '#3B82F6', label: 'Stocks' },
                          { value: demoData.portfolio.bonds, color: '#10B981', label: 'Bonds' },
                          { value: demoData.portfolio.alternatives, color: '#F59E0B', label: 'Alternatives' },
                          { value: demoData.portfolio.cash, color: '#6B7280', label: 'Cash' }
                        ]}
                        size={200}
                      />
                    </div>
                    
                    <div className="space-y-4">
                      {[
                        { label: 'Stocks', value: demoData.portfolio.stocks, color: 'bg-blue-500' },
                        { label: 'Bonds', value: demoData.portfolio.bonds, color: 'bg-green-500' },
                        { label: 'Alternatives', value: demoData.portfolio.alternatives, color: 'bg-yellow-500' },
                        { label: 'Cash', value: demoData.portfolio.cash, color: 'bg-gray-500' }
                      ].map(({ label, value, color }) => (
                        <div key={label} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className={`w-4 h-4 rounded ${color}`} />
                            <span className="font-medium">{label}</span>
                          </div>
                          <span className="text-lg font-bold">{value}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Detailed breakdown */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Detailed Asset Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {Object.entries(demoData.portfolio.breakdown).map(([asset, percentage]) => (
                      <motion.div
                        key={asset}
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.4 }}
                        className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg"
                      >
                        <h4 className="font-semibold mb-2 capitalize">
                          {asset.replace(/([A-Z])/g, ' $1').trim()}
                        </h4>
                        <div className="text-2xl font-bold text-blue-600 mb-2">
                          {percentage}%
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* AI recommendations */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    AI Portfolio Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {demoData.simulation.recommendations.map((rec, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="flex items-start gap-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg"
                      >
                        <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
                        <div>
                          <h4 className="font-semibold mb-1">{rec.title}</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{rec.description}</p>
                          <div className="flex gap-2">
                            <Badge variant={rec.priority === 'high' ? 'default' : 'secondary'}>
                              {rec.priority} priority
                            </Badge>
                            <Badge variant="outline">
                              {rec.impact} impact
                            </Badge>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Goal Tracking Section */}
      <section id="goals" className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Goal Tracking & Progress</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Visual progress tracking with smart milestone celebrations
            </p>
          </motion.div>

          <div className="max-w-6xl mx-auto space-y-8">
            {/* Goals overview */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {demoData.goals.map((goal, index) => (
                <motion.div
                  key={goal.id}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="h-full">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-lg">{goal.title}</CardTitle>
                        <Badge variant={goal.priority === 'high' ? 'default' : 'secondary'}>
                          {goal.priority}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="flex justify-between text-sm mb-2">
                            <span>Progress</span>
                            <span>{goal.progress}%</span>
                          </div>
                          <Progress value={goal.progress} className="h-3" />
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-center">
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Current</p>
                            <p className="font-semibold">
                              <AnimatedNumber value={goal.currentAmount} prefix="$" />
                            </p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Target</p>
                            <p className="font-semibold">
                              <AnimatedNumber value={goal.targetAmount} prefix="$" />
                            </p>
                          </div>
                        </div>
                        
                        <div className="text-center">
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Monthly Contribution</p>
                          <p className="text-lg font-bold text-green-600">
                            <AnimatedNumber value={goal.monthlyContribution} prefix="$" />
                          </p>
                        </div>
                        
                        <div className="text-center">
                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Target Date</p>
                          <p className="font-medium">{new Date(goal.targetDate).toLocaleDateString()}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>

            {/* Goal analysis from simulation */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Goal Achievement Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {demoData.simulation.goalAnalysis.map((analysis, index) => {
                      const goal = demoData.goals.find(g => g.id === analysis.goalId);
                      if (!goal) return null;
                      
                      return (
                        <motion.div
                          key={analysis.goalId}
                          initial={{ opacity: 0, x: -20 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="border rounded-lg p-4"
                        >
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold">{goal.title}</h4>
                            <Badge variant={analysis.achievementProbability > 80 ? 'default' : 'secondary'}>
                              {analysis.achievementProbability}% Success Rate
                            </Badge>
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="text-center">
                              <p className="text-sm text-gray-600 dark:text-gray-400">Achievement Probability</p>
                              <div className="text-2xl font-bold text-green-600">
                                {analysis.achievementProbability}%
                              </div>
                              <Progress value={analysis.achievementProbability} className="mt-2" />
                            </div>
                            
                            <div className="text-center">
                              <p className="text-sm text-gray-600 dark:text-gray-400">Projected Completion</p>
                              <p className="font-semibold">
                                {new Date(analysis.projectedCompletionDate).toLocaleDateString()}
                              </p>
                            </div>
                            
                            <div className="text-center">
                              <p className="text-sm text-gray-600 dark:text-gray-400">Recommended Adjustment</p>
                              <p className={`font-semibold ${analysis.recommendedAdjustment > 0 ? 'text-orange-600' : 'text-green-600'}`}>
                                {analysis.recommendedAdjustment > 0 ? '+' : ''}
                                <AnimatedNumber value={analysis.recommendedAdjustment} prefix="$" suffix="/month" />
                              </p>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Risk Assessment Section */}
      <section id="risk" className="py-20 bg-white dark:bg-gray-900">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Risk Assessment & Management</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Comprehensive risk analysis with dynamic stress testing
            </p>
          </motion.div>

          <div className="max-w-6xl mx-auto space-y-8">
            {/* Risk metrics */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
            >
              {[
                { 
                  label: 'Portfolio Volatility', 
                  value: demoData.simulation.riskMetrics.volatility, 
                  suffix: '%',
                  color: 'text-orange-600',
                  description: 'Expected annual fluctuation'
                },
                { 
                  label: 'Max Drawdown', 
                  value: Math.abs(demoData.simulation.riskMetrics.maxDrawdown), 
                  suffix: '%',
                  color: 'text-red-600',
                  description: 'Worst case scenario loss'
                },
                { 
                  label: 'Sharpe Ratio', 
                  value: demoData.simulation.riskMetrics.sharpeRatio, 
                  suffix: '',
                  color: 'text-green-600',
                  description: 'Risk-adjusted returns'
                },
                { 
                  label: 'Beta Coefficient', 
                  value: demoData.simulation.riskMetrics.beta, 
                  suffix: '',
                  color: 'text-blue-600',
                  description: 'Market correlation'
                }
              ].map(({ label, value, suffix, color, description }, index) => (
                <motion.div
                  key={label}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="text-center h-full">
                    <CardContent className="p-6">
                      <Shield className={`h-8 w-8 mx-auto mb-3 ${color}`} />
                      <h3 className="font-semibold mb-2">{label}</h3>
                      <div className={`text-2xl font-bold ${color} mb-2`}>
                        <AnimatedNumber value={value} suffix={suffix} />
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{description}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>

            {/* Trade-off scenarios */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Risk vs. Return Trade-off Scenarios
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {demoTradeOffScenarios.map((scenario, index) => (
                      <motion.div
                        key={scenario.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className="border rounded-lg p-4 hover:shadow-lg transition-shadow"
                      >
                        <h4 className="font-semibold mb-2">{scenario.title}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{scenario.description}</p>
                        
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm">Expected Return</span>
                            <span className="font-semibold text-green-600">
                              {scenario.projectedOutcome.expectedReturn}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">Success Rate</span>
                            <span className="font-semibold text-blue-600">
                              {scenario.projectedOutcome.goalAchievementProbability}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm">Volatility</span>
                            <span className="font-semibold text-orange-600">
                              {scenario.projectedOutcome.volatility}%
                            </span>
                          </div>
                        </div>
                        
                        <div className="mt-4 pt-4 border-t">
                          <div className="flex items-center justify-between text-sm">
                            <span>Risk Level</span>
                            <Badge variant={
                              scenario.impact.risk === 'increased' ? 'destructive' :
                              scenario.impact.risk === 'reduced' ? 'default' : 'secondary'
                            }>
                              {scenario.impact.risk}
                            </Badge>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Risk tolerance assessment */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle>Your Risk Profile</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <h4 className="font-semibold mb-4">Current Risk Tolerance: 
                        <span className="ml-2 capitalize text-blue-600">{demoData.profile.riskTolerance}</span>
                      </h4>
                      
                      <div className="space-y-4">
                        {[
                          { label: 'Conservative', value: 20, active: demoData.profile.riskTolerance === 'conservative' },
                          { label: 'Moderate', value: 60, active: demoData.profile.riskTolerance === 'moderate' },
                          { label: 'Aggressive', value: 85, active: demoData.profile.riskTolerance === 'aggressive' }
                        ].map(({ label, value, active }) => (
                          <div key={label} className={`p-3 rounded ${active ? 'bg-blue-50 dark:bg-blue-950' : 'bg-gray-50 dark:bg-gray-800'}`}>
                            <div className="flex justify-between mb-2">
                              <span className="font-medium">{label}</span>
                              <span>{value}% Equity</span>
                            </div>
                            <Progress value={value} className="h-2" />
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold mb-4">Risk Insights</h4>
                      <div className="space-y-3">
                        <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-950 rounded">
                          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                          <div>
                            <p className="font-medium">Appropriate Risk Level</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Your portfolio matches your stated risk tolerance
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-950 rounded">
                          <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
                          <div>
                            <p className="font-medium">Diversification Benefits</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Your current allocation reduces risk through diversification
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950 rounded">
                          <DollarSign className="h-5 w-5 text-yellow-600 mt-0.5" />
                          <div>
                            <p className="font-medium">Rebalancing Opportunity</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Consider rebalancing quarterly to maintain target allocation
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Gamification & Achievements */}
      <section id="achievements" className="py-20 bg-gray-50 dark:bg-gray-800">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Achievements & Progress</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Gamification elements to keep you motivated and engaged
            </p>
          </motion.div>

          <div className="max-w-6xl mx-auto space-y-8">
            {/* Level and progress */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Card className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950 dark:to-blue-950">
                <CardContent className="p-8">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {demoData.achievements.level.current}
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold">Financial Planning Level {demoData.achievements.level.current}</h3>
                        <p className="text-gray-600 dark:text-gray-400">
                          {demoData.achievements.level.pointsToNext} points to level {demoData.achievements.level.nextLevel}
                        </p>
                      </div>
                    </div>
                    <Trophy className="h-12 w-12 text-yellow-500" />
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span>Level Progress</span>
                      <span>{demoData.achievements.level.progress}%</span>
                    </div>
                    <Progress value={demoData.achievements.level.progress} className="h-3" />
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Achievement badges */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="h-5 w-5" />
                    Achievement Badges
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {demoData.achievements.badges.map((badge, index) => (
                      <motion.div
                        key={badge.id}
                        initial={{ opacity: 0, scale: 0.8 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className={`text-center p-6 rounded-lg ${
                          badge.earned 
                            ? 'bg-gradient-to-b from-yellow-50 to-orange-50 dark:from-yellow-950 dark:to-orange-950 border-yellow-200' 
                            : 'bg-gray-50 dark:bg-gray-800 border-gray-200'
                        } border`}
                      >
                        <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
                          badge.earned ? 'bg-gradient-to-r from-yellow-400 to-orange-500' : 'bg-gray-300'
                        }`}>
                          {badge.earned ? (
                            <Star className="h-8 w-8 text-white" />
                          ) : (
                            <Star className="h-8 w-8 text-gray-500" />
                          )}
                        </div>
                        <h4 className={`font-semibold mb-2 ${badge.earned ? 'text-yellow-700 dark:text-yellow-300' : 'text-gray-500'}`}>
                          {badge.title}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                          {badge.description}
                        </p>
                        {badge.earned ? (
                          <Badge className="bg-yellow-100 text-yellow-800">
                            Earned {badge.earnedDate}
                          </Badge>
                        ) : (
                          badge.progress && (
                            <div className="space-y-2">
                              <Progress value={badge.progress} className="h-2" />
                              <p className="text-xs text-gray-500">{badge.progress}% complete</p>
                            </div>
                          )
                        )}
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Streaks and habits */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Streaks & Habits
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                      { 
                        label: 'Savings Streak', 
                        current: demoData.achievements.streaks.savings.current,
                        best: demoData.achievements.streaks.savings.best,
                        icon: DollarSign,
                        color: 'text-green-600'
                      },
                      { 
                        label: 'Goal Progress', 
                        current: demoData.achievements.streaks.goalProgress.current,
                        best: demoData.achievements.streaks.goalProgress.best,
                        icon: Target,
                        color: 'text-blue-600'
                      },
                      { 
                        label: 'App Usage', 
                        current: demoData.achievements.streaks.appUsage.current,
                        best: demoData.achievements.streaks.appUsage.best,
                        icon: Sparkles,
                        color: 'text-purple-600'
                      }
                    ].map(({ label, current, best, icon: Icon, color }, index) => (
                      <motion.div
                        key={label}
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg border"
                      >
                        <Icon className={`h-8 w-8 mx-auto mb-3 ${color}`} />
                        <h4 className="font-semibold mb-2">{label}</h4>
                        <div className="space-y-2">
                          <div>
                            <p className="text-2xl font-bold">{current}</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Current streak</p>
                          </div>
                          <div>
                            <p className="text-lg font-semibold text-gray-700 dark:text-gray-300">{best}</p>
                            <p className="text-xs text-gray-500">Best streak</p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Call to action */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="text-center"
            >
              <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
                <CardContent className="p-8">
                  <Gift className="h-12 w-12 mx-auto mb-4 text-blue-600" />
                  <h3 className="text-2xl font-bold mb-4">Ready to Start Your Financial Journey?</h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-2xl mx-auto">
                    This demo showcases the power of AI-driven financial planning. Start your personalized journey today 
                    with comprehensive analysis, goal tracking, and intelligent recommendations.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
                      <Users className="mr-2 h-5 w-5" />
                      Get Started Free
                    </Button>
                    <Button size="lg" variant="outline" onClick={exportToPDF}>
                      <Download className="mr-2 h-5 w-5" />
                      Download Full Report
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Floating action buttons */}
      <div className="fixed bottom-6 right-6 flex flex-col gap-3 z-40">
        <Button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          className="w-12 h-12 rounded-full shadow-lg"
          size="sm"
        >
          ↑
        </Button>
        <Button
          onClick={() => setIsAutoPlaying(!isAutoPlaying)}
          variant={isAutoPlaying ? "default" : "outline"}
          className="w-12 h-12 rounded-full shadow-lg"
          size="sm"
        >
          {isAutoPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </Button>
      </div>

      {/* Progress indicator */}
      <div className="fixed bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700 z-50">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-600 to-purple-600"
          style={{
            width: `${((currentSection + 1) / sections.length) * 100}%`
          }}
          transition={{ duration: 0.3 }}
        />
      </div>
    </div>
  );
}