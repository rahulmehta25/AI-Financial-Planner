import React from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";

const INSIGHTS = [
  { text: "Your savings rate of 22% exceeds the recommended 20% target. Consider maxing your Roth IRA contribution.", tag: "Savings" },
  { text: "US equities (42%) are slightly overweight vs your target 40%. Rebalancing could reduce concentration risk.", tag: "Portfolio" },
  { text: "You have $14,200 in capital losses available for tax-loss harvesting before year end.", tag: "Tax" },
  { text: "At your current contribution rate, you'll reach your retirement goal 3 years ahead of schedule.", tag: "Retirement" },
];

const QuickAIInsight: React.FC = () => {
  const navigate = useNavigate();
  const insight = INSIGHTS[Math.floor(Date.now() / 86400000) % INSIGHTS.length];

  return (
    <div
      id="quick-ai-insight-card"
      className="metric-card relative overflow-hidden"
      style={{
        background: "linear-gradient(135deg, hsl(214 100% 10% / 0.9) 0%, hsl(220 40% 8% / 0.9) 100%)",
        borderColor: "hsl(214 100% 57% / 0.2)",
      }}
    >
      {/* Glow orb */}
      <div
        id="ai-insight-glow"
        className="absolute -top-8 -right-8 w-32 h-32 rounded-full opacity-20 pointer-events-none"
        style={{ background: "radial-gradient(circle, hsl(214 100% 57%) 0%, transparent 70%)" }}
      />

      <div id="ai-insight-content" className="relative">
        {/* Header */}
        <div id="ai-insight-header" className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div>
            <p className="text-xs font-semibold text-blue-300 uppercase tracking-widest">AI Insight</p>
          </div>
          <span id="ai-insight-tag" className="ml-auto badge-gold text-[10px]">{insight.tag}</span>
        </div>

        {/* Insight text */}
        <p id="ai-insight-text" className="text-sm text-foreground/90 leading-relaxed mb-4">
          {insight.text}
        </p>

        {/* CTA */}
        <Button
          id="ai-insight-cta"
          variant="ghost"
          size="sm"
          onClick={() => navigate("/ai-advisor")}
          className="h-8 px-3 text-xs text-blue-300 hover:text-blue-200 hover:bg-blue-500/10 border border-blue-500/20 hover:border-blue-500/40 w-full justify-between"
        >
          <span className="flex items-center gap-1.5">
            <Bot className="w-3 h-3" />
            Ask AI for more insights
          </span>
          <ArrowRight className="w-3 h-3" />
        </Button>
      </div>
    </div>
  );
};

export default QuickAIInsight;
