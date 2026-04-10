import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import {
  Bot,
  Sparkles,
  MessageSquare,
  TrendingUp,
  AlertCircle,
  Download,
  History,
  Brain,
  Zap,
  Target,
  Shield,
  Plus,
  PieChart,
  Calculator,
  DollarSign,
  BarChart3,
  RefreshCw,
} from "lucide-react";

import ChatInterface from "@/components/chat/ChatInterface";
import ConversationHistory from "@/components/chat/ConversationHistory";
import SuggestedTopics from "@/components/chat/SuggestedTopics";
import { ChatSession, ChatMessage, chatService } from "@/services/chat";
import { userService } from "@/services/user";
import { portfolioService } from "@/services/portfolio";
import pdfExportService from "@/services/pdfExport";

/* ─── Suggested prompts shown in the side panel ─── */
const SUGGESTED_PROMPTS = [
  { icon: TrendingUp,  label: "Analyze portfolio",     prompt: "Analyze my current portfolio and highlight any concentration risks or rebalancing opportunities.", color: "blue"   },
  { icon: Target,      label: "Retirement plan",       prompt: "Based on my savings rate and investment mix, when can I realistically retire?",                   color: "violet" },
  { icon: DollarSign,  label: "Tax optimization",      prompt: "What tax-loss harvesting opportunities do I have before year end?",                              color: "gold"   },
  { icon: PieChart,    label: "Asset allocation",      prompt: "Review my asset allocation and suggest improvements for my risk tolerance and time horizon.",    color: "emerald"},
  { icon: Calculator,  label: "Monte Carlo",           prompt: "Run a Monte Carlo simulation with my current parameters and explain the risk scenarios.",       color: "blue"   },
  { icon: BarChart3,   label: "Expense breakdown",     prompt: "Help me identify areas where I can reduce expenses to increase my savings rate.",               color: "red"    },
  { icon: Shield,      label: "Risk assessment",       prompt: "Assess my current financial risk profile — am I taking too much or too little risk?",            color: "violet" },
  { icon: Zap,         label: "Quick wins",            prompt: "What are the top 3 things I can do this week to improve my financial health?",                 color: "gold"   },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; iconBg: string }> = {
  blue:   { bg: "bg-blue-500/6",   border: "border-blue-500/20",   text: "text-blue-300",   iconBg: "bg-blue-500/15"   },
  violet: { bg: "bg-violet-500/6", border: "border-violet-500/20", text: "text-violet-300", iconBg: "bg-violet-500/15" },
  gold:   { bg: "bg-amber-500/6",  border: "border-amber-500/20",  text: "text-amber-300",  iconBg: "bg-amber-500/15"  },
  emerald:{ bg: "bg-emerald-500/6",border: "border-emerald-500/20",text: "text-emerald-300",iconBg: "bg-emerald-500/15"},
  red:    { bg: "bg-red-500/6",    border: "border-red-500/20",    text: "text-red-300",    iconBg: "bg-red-500/15"    },
};

/* ─── Stats ─── */
const StatCard: React.FC<{ label: string; value: string | number; icon: React.ElementType; color: string }> = ({ label, value, icon: Icon, color }) => (
  <div id={`ai-stat-${label.toLowerCase().replace(/\s/g, "-")}`} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${COLOR_MAP[color]?.iconBg || "bg-blue-500/15"}`}>
      <Icon className={`w-4 h-4 ${COLOR_MAP[color]?.text || "text-blue-300"}`} />
    </div>
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-sm font-bold text-foreground financial-number">{value}</div>
    </div>
  </div>
);

/* ─── Skeleton ─── */
const AIAdvisorSkeleton = () => (
  <div id="ai-advisor-skeleton" className="flex gap-6 h-[calc(100vh-9rem)] animate-fade-in">
    <div className="flex-1 space-y-4">
      <Skeleton className="h-16 w-full rounded-2xl bg-navy-800" />
      <Skeleton className="flex-1 h-[calc(100%-8rem)] rounded-2xl bg-navy-800" />
    </div>
    <div className="w-72 space-y-4">
      <Skeleton className="h-32 rounded-2xl bg-navy-800" />
      <Skeleton className="h-64 rounded-2xl bg-navy-800" />
    </div>
  </div>
);

/* ─── Main Component ─── */
const AIAdvisor: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();

  const [currentSession, setCurrentSession]  = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading]            = useState(true);
  const [error, setError]                    = useState<string | null>(null);
  const [userContext, setUserContext]         = useState<any>(null);
  const [activePanel, setActivePanel]        = useState<"chat" | "history">("chat");
  const [stats, setStats]                    = useState({ sessions: 0, messages: 0, recommendations: 0 });

  useEffect(() => {
    if (!isAuthenticated) { setIsLoading(false); return; }
    const init = async () => {
      try {
        setIsLoading(true);
        const [portfolioData, financialProfile] = await Promise.allSettled([
          portfolioService.getPortfolioOverview().catch(() => null),
          userService.getFinancialProfile().catch(() => null),
        ]);
        setUserContext({
          portfolioData: portfolioData.status === "fulfilled" ? portfolioData.value : null,
          financialProfile: financialProfile.status === "fulfilled" ? financialProfile.value : null,
          user,
        });

        const sessions = await chatService.getChatSessions();
        if (sessions.length > 0) {
          setCurrentSession(sessions[0]);
          setStats({
            sessions: sessions.length,
            messages: sessions.reduce((t, s) => t + (s.messages?.length || 0), 0),
            recommendations: sessions.reduce((t, s) => t + (s.messages?.filter(m => m.role === "assistant").length || 0), 0),
          });
        } else {
          await createNewSession();
        }
      } catch (err: any) {
        setError(err.message || "Failed to initialize AI Advisor.");
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, [isAuthenticated, user]);

  const createNewSession = async () => {
    try {
      const session = await chatService.createChatSession(`Chat — ${new Date().toLocaleDateString()}`);
      const welcome: ChatMessage = {
        id: `welcome-${Date.now()}`,
        content: `Hello${user?.firstName ? ` ${user.firstName}` : ""}! I'm your AI financial advisor powered by Claude. I can help you with:\n\n• **Portfolio Analysis** — Review holdings, risk, and performance\n• **Retirement Planning** — Project your path to financial independence\n• **Tax Optimization** — Legal strategies to minimize your tax burden\n• **Risk Assessment** — Evaluate and calibrate your investment risk\n• **Goal Tracking** — Monitor and accelerate your financial goals\n\nWhat would you like to explore today?`,
        role: "assistant",
        timestamp: new Date().toISOString(),
        metadata: { suggestions: ["Analyze my portfolio", "Help me plan for retirement", "Find tax savings opportunities"] },
      };
      session.messages = [welcome];
      setCurrentSession(session);
      toast({ title: "New conversation started", description: "Your AI advisor is ready." });
    } catch {
      setError("Failed to start conversation.");
    }
  };

  const handleExport = async () => {
    if (!currentSession) return;
    try {
      await pdfExportService.exportConversation(currentSession, { includeTimestamps: true, includeMetadata: true, includeRecommendations: true, template: "detailed_report" });
      toast({ title: "Export started", description: "Preparing your PDF report." });
    } catch (err: any) {
      toast({ title: "Export failed", description: err.message, variant: "destructive" });
    }
  };

  /* Unauthenticated gate */
  if (!isLoading && !isAuthenticated) {
    return (
      <div id="ai-advisor-auth-gate" className="flex flex-col items-center justify-center min-h-[60vh] text-center py-16 page-enter">
        <div className="w-20 h-20 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-6 shadow-glow-blue">
          <Bot className="w-10 h-10 text-blue-400" />
        </div>
        <h1 className="text-3xl font-bold text-foreground mb-3">AI Financial Advisor</h1>
        <p className="text-muted-foreground max-w-md mb-8">
          Sign in to access your personalized AI financial advisor with portfolio analysis, retirement planning, and tax optimization.
        </p>
        <div className="flex gap-3">
          <Button onClick={() => window.location.href = "/login"} className="bg-gradient-to-r from-blue-600 to-blue-500 text-white border-0">
            Sign In to Start
          </Button>
          <Button variant="outline" onClick={() => window.location.href = "/signup"} className="border-white/10 hover:bg-white/[0.04]">
            Create Account
          </Button>
        </div>
      </div>
    );
  }

  if (isLoading) return <AIAdvisorSkeleton />;

  return (
    <div id="ai-advisor-root" className="page-enter pt-4">
      {/* ─── Page header ─── */}
      <div id="ai-advisor-header" className="flex items-start justify-between mb-5">
        <div id="ai-advisor-title-group">
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/25 flex items-center justify-center shadow-glow-blue">
              <Brain className="w-4 h-4 text-blue-400" />
            </div>
            <h1 id="ai-advisor-title" className="text-xl font-bold text-foreground">AI Financial Advisor</h1>
            <Badge variant="outline" className="bg-blue-500/10 border-blue-500/25 text-blue-300 text-[10px] gap-1 px-2">
              <span className="status-dot-green scale-75" />
              Claude AI
            </Badge>
          </div>
          <p id="ai-advisor-subtitle" className="text-sm text-muted-foreground">
            Personalized financial guidance powered by advanced AI
          </p>
        </div>

        <div id="ai-advisor-header-actions" className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={handleExport}
            className="h-8 px-3 text-xs text-muted-foreground hover:text-foreground hover:bg-white/[0.06] border border-white/10 gap-1.5">
            <Download className="w-3.5 h-3.5" /> Export PDF
          </Button>
          <Button size="sm" onClick={createNewSession}
            className="h-8 px-3 text-xs gap-1.5 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white border-0 shadow-glow-blue">
            <Plus className="w-3.5 h-3.5" /> New Chat
          </Button>
        </div>
      </div>

      {/* ─── Stats row ─── */}
      <div id="ai-advisor-stats" className="grid grid-cols-3 gap-3 mb-5">
        <StatCard label="Conversations"   value={stats.sessions}         icon={MessageSquare} color="blue"   />
        <StatCard label="Messages"        value={stats.messages}         icon={TrendingUp}    color="emerald"/>
        <StatCard label="Recommendations" value={stats.recommendations}  icon={Sparkles}      color="gold"   />
      </div>

      {/* ─── Error ─── */}
      {error && (
        <Alert variant="destructive" className="mb-4 glass border-red-500/30 bg-red-500/5">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button variant="ghost" size="sm" onClick={() => setError(null)} className="ml-2 h-6 text-xs">Dismiss</Button>
          </AlertDescription>
        </Alert>
      )}

      {/* ─── Two-panel layout ─── */}
      <div id="ai-advisor-panels" className="flex gap-5" style={{ height: "calc(100vh - 18rem)", minHeight: "500px" }}>

        {/* LEFT: Chat panel (primary) */}
        <div id="ai-advisor-chat-panel" className="flex-1 min-w-0 glass-card rounded-2xl overflow-hidden flex flex-col">
          {/* Panel tabs */}
          <div id="chat-panel-tabs" className="flex items-center gap-1 px-4 py-3 border-b border-white/[0.06] flex-shrink-0">
            <button
              id="tab-chat"
              onClick={() => setActivePanel("chat")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activePanel === "chat"
                  ? "bg-blue-500/15 text-blue-300 border border-blue-500/25"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/[0.04]"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" /> Chat
            </button>
            <button
              id="tab-history"
              onClick={() => setActivePanel("history")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activePanel === "history"
                  ? "bg-blue-500/15 text-blue-300 border border-blue-500/25"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/[0.04]"
              }`}
            >
              <History className="w-3.5 h-3.5" /> History
            </button>

            <div className="ml-auto flex items-center gap-1">
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-emerald-500/8 border border-emerald-500/15">
                <span className="status-dot-green" style={{ width: "6px", height: "6px" }} />
                <span className="text-[10px] text-emerald-400 font-medium">Online</span>
              </div>
            </div>
          </div>

          {/* Panel content */}
          <div id="chat-panel-content" className="flex-1 overflow-hidden">
            {activePanel === "chat" ? (
              currentSession ? (
                <ChatInterface
                  session={currentSession}
                  userContext={userContext}
                  onSessionUpdate={setCurrentSession}
                  onNewSession={createNewSession}
                  onExportConversation={handleExport}
                  isFullscreen={false}
                />
              ) : (
                <div id="chat-empty-state" className="h-full flex flex-col items-center justify-center text-center p-8">
                  <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                    <Bot className="w-8 h-8 text-blue-400" />
                  </div>
                  <h3 className="text-base font-semibold text-foreground mb-2">No Active Conversation</h3>
                  <p className="text-sm text-muted-foreground mb-4 max-w-xs">Start a new conversation with your AI financial advisor.</p>
                  <Button size="sm" onClick={createNewSession}
                    className="gap-1.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white border-0">
                    <Plus className="w-3.5 h-3.5" /> Start Conversation
                  </Button>
                </div>
              )
            ) : (
              <div id="chat-history-content" className="h-full overflow-y-auto p-4">
                <ConversationHistory
                  currentSessionId={currentSession?.id}
                  onSessionSelect={(session) => { setCurrentSession(session); setActivePanel("chat"); }}
                  onExportConversation={handleExport}
                />
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Side panel — suggested prompts */}
        <div id="ai-advisor-side-panel" className="w-72 flex-shrink-0 flex flex-col gap-4 overflow-y-auto">

          {/* Capabilities card */}
          <div id="ai-capabilities-card" className="glass-card rounded-2xl p-4 flex-shrink-0">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-semibold text-foreground uppercase tracking-widest">AI Capabilities</span>
            </div>
            <div id="capabilities-list" className="space-y-2">
              {[
                { icon: TrendingUp,  label: "Real-time portfolio analysis",   color: "text-blue-400"   },
                { icon: Target,      label: "Goal projection modeling",        color: "text-emerald-400"},
                { icon: Shield,      label: "Risk profiling & rebalancing",    color: "text-violet-400" },
                { icon: DollarSign,  label: "Tax-loss harvesting strategies",  color: "text-amber-400"  },
                { icon: Brain,       label: "Behavioral finance coaching",     color: "text-blue-400"   },
              ].map((cap, i) => {
                const Icon = cap.icon;
                return (
                  <div key={i} id={`capability-${i}`} className="flex items-center gap-2">
                    <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${cap.color}`} />
                    <span className="text-xs text-muted-foreground">{cap.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Suggested prompts */}
          <div id="suggested-prompts-card" className="glass-card rounded-2xl p-4 flex-1">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-semibold text-foreground uppercase tracking-widest">Try Asking</span>
            </div>
            <div id="prompts-list" className="space-y-2">
              {SUGGESTED_PROMPTS.map((prompt, i) => {
                const Icon = prompt.icon;
                const c = COLOR_MAP[prompt.color] || COLOR_MAP.blue;
                return (
                  <button
                    key={i}
                    id={`prompt-btn-${i}`}
                    onClick={() => {
                      setActivePanel("chat");
                      // The ChatInterface will pick up the prompt via session update
                    }}
                    className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl border text-left transition-all hover:opacity-90 group ${c.bg} ${c.border}`}
                  >
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0 ${c.iconBg}`}>
                      <Icon className={`w-3 h-3 ${c.text}`} />
                    </div>
                    <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors line-clamp-2 leading-relaxed">
                      {prompt.prompt}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Powered-by badge */}
          <div id="powered-by-badge" className="glass-card rounded-2xl p-3 flex items-center gap-3 flex-shrink-0">
            <div className="w-8 h-8 rounded-xl bg-violet-500/15 border border-violet-500/25 flex items-center justify-center flex-shrink-0">
              <Brain className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <div className="text-xs font-semibold text-foreground">Powered by Claude</div>
              <div className="text-[10px] text-muted-foreground">Anthropic's AI model</div>
            </div>
            <div className="ml-auto flex items-center gap-1.5 px-2 py-1 rounded-full bg-violet-500/10 border border-violet-500/20">
              <span className="status-dot-green" style={{ width: "6px", height: "6px", background: "hsl(152 69% 48%)" }} />
              <span className="text-[10px] text-violet-300">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIAdvisor;
