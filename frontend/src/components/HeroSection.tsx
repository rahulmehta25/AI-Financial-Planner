import { Button } from "@/components/ui/button";
import { TypewriterText } from "./TypewriterText";
import { ArrowRight, TrendingUp, Shield, Brain } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useDemo } from "@/contexts/DemoContext";

export const HeroSection = () => {
  const navigate = useNavigate();
  const { enableDemoMode } = useDemo();

  return (
    <section className="relative min-h-screen flex items-center justify-center px-6 overflow-hidden">
      {/* Animated background gradients */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-success/10" />
      
      {/* Floating shapes */}
      <div className="absolute top-20 left-10 w-32 h-32 rounded-full bg-primary/20 blur-xl animate-float" />
      <div className="absolute bottom-20 right-10 w-24 h-24 rounded-full bg-success/20 blur-xl animate-float" style={{ animationDelay: '2s' }} />
      <div className="absolute top-1/2 left-1/4 w-16 h-16 rounded-full bg-warning/20 blur-xl animate-float" style={{ animationDelay: '4s' }} />

      <div className="relative z-10 text-center max-w-6xl mx-auto">
        {/* Main heading with typewriter effect */}
        <h1 className="text-6xl md:text-8xl font-bold mb-8 leading-tight">
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary to-success">
            AI-Powered
          </span>
          <br />
          <TypewriterText 
            words={["Financial", "Investment", "Wealth", "Portfolio"]}
            className="text-foreground"
          />
          <br />
          <span className="text-foreground">Planning</span>
        </h1>

        {/* Subtitle */}
        <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-3xl mx-auto animate-slide-in-bottom" style={{ animationDelay: '0.5s' }}>
          Transform your financial future with intelligent planning, real-time insights, 
          and AI-driven recommendations tailored to your unique goals.
        </p>

        {/* Feature highlights */}
        <div className="flex flex-wrap justify-center gap-8 mb-12 animate-slide-in-bottom" style={{ animationDelay: '1s' }}>
          <div className="flex items-center gap-3 glass rounded-full px-6 py-3">
            <Brain className="w-5 h-5 text-primary" />
            <span className="text-sm font-medium">AI-Powered Insights</span>
          </div>
          <div className="flex items-center gap-3 glass rounded-full px-6 py-3">
            <TrendingUp className="w-5 h-5 text-success" />
            <span className="text-sm font-medium">Real-time Analytics</span>
          </div>
          <div className="flex items-center gap-3 glass rounded-full px-6 py-3">
            <Shield className="w-5 h-5 text-warning" />
            <span className="text-sm font-medium">Bank-level Security</span>
          </div>
        </div>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-in-bottom" style={{ animationDelay: '1.5s' }}>
          <Button 
            size="lg" 
            className="group relative overflow-hidden bg-gradient-to-r from-primary to-primary-hover hover:shadow-glow transition-all duration-300 px-8 py-6 text-lg"
            onClick={() => navigate('/dashboard')}
          >
            Get Started Free
            <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
          
          <Button 
            variant="outline" 
            size="lg"
            className="glass hover:bg-white/10 border-white/20 px-8 py-6 text-lg"
            onClick={() => {
              enableDemoMode();
              navigate('/dashboard');
            }}
          >
            View Demo
          </Button>
        </div>

        {/* Stats */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 animate-slide-in-bottom" style={{ animationDelay: '2s' }}>
          <div className="text-center">
            <div className="text-4xl font-bold text-primary mb-2">$2.5B+</div>
            <div className="text-muted-foreground">Assets Under Management</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-success mb-2">50K+</div>
            <div className="text-muted-foreground">Active Users</div>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-warning mb-2">98%</div>
            <div className="text-muted-foreground">Customer Satisfaction</div>
          </div>
        </div>
      </div>
    </section>
  );
};