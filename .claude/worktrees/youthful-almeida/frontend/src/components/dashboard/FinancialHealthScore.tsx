import React from "react";
import { ShieldCheck, TrendingUp, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";

interface HealthMetric {
  label: string;
  value: string;
  status: "good" | "warn" | "bad";
  detail?: string;
}

const METRICS: HealthMetric[] = [
  { label: "Savings Rate",      value: "22%",   status: "good", detail: "Target: 20%+" },
  { label: "Emergency Fund",    value: "7 mo",  status: "good", detail: "Recommended: 6 mo" },
  { label: "Debt-to-Income",    value: "18%",   status: "good", detail: "Target: <35%" },
  { label: "Investment Ratio",  value: "31%",   status: "good", detail: "Of gross income" },
  { label: "Insurance Coverage",value: "Partial",status: "warn",detail: "Review life insurance" },
  { label: "Estate Planning",   value: "None",  status: "bad",  detail: "No will on file" },
];

const StatusIcon: React.FC<{ status: HealthMetric["status"] }> = ({ status }) => {
  if (status === "good") return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
  if (status === "warn") return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
  return <XCircle className="w-3.5 h-3.5 text-red-400" />;
};

const getGradeConfig = (score: number) => {
  if (score >= 90) return { grade: "A+", label: "Excellent",  classes: "health-score-a",   textColor: "text-emerald-300" };
  if (score >= 80) return { grade: "A",  label: "Great",      classes: "health-score-a",   textColor: "text-emerald-300" };
  if (score >= 70) return { grade: "B+", label: "Good",       classes: "health-score-b",   textColor: "text-blue-300"   };
  if (score >= 60) return { grade: "B",  label: "Fair",       classes: "health-score-b",   textColor: "text-blue-300"   };
  if (score >= 50) return { grade: "C",  label: "Average",    classes: "health-score-c",   textColor: "text-amber-300"  };
  return              { grade: "D",  label: "Needs Work", classes: "health-score-d",   textColor: "text-red-300"    };
};

interface FinancialHealthScoreProps {
  score?: number;
}

const FinancialHealthScore: React.FC<FinancialHealthScoreProps> = ({ score = 82 }) => {
  const config = getGradeConfig(score);
  const goodCount = METRICS.filter(m => m.status === "good").length;

  return (
    <div id="financial-health-card" className="metric-card">
      <div id="financial-health-header" className="flex items-start justify-between mb-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Financial Health</p>
          <h3 className="text-lg font-bold text-foreground">Score Card</h3>
        </div>

        {/* Grade badge */}
        <div id="health-grade-badge" className={`w-14 h-14 rounded-2xl ${config.classes} flex flex-col items-center justify-center flex-shrink-0`}>
          <span className={`text-2xl font-black leading-none ${config.textColor}`}>{config.grade}</span>
          <span className="text-[9px] text-white/70 uppercase tracking-wide mt-0.5">{config.label}</span>
        </div>
      </div>

      {/* Score bar */}
      <div id="health-score-bar" className="mb-5">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-muted-foreground">Health Score</span>
          <span className="font-bold text-foreground financial-number">{score}/100</span>
        </div>
        <div className="h-2 bg-navy-800 rounded-full overflow-hidden">
          <div
            id="health-score-fill"
            className="h-full rounded-full transition-all duration-1000"
            style={{
              width: `${score}%`,
              background: "linear-gradient(90deg, hsl(214 100% 50%) 0%, hsl(152 69% 45%) 100%)",
            }}
          />
        </div>
        <div className="flex items-center gap-1 mt-2">
          <ShieldCheck className="w-3 h-3 text-emerald-400" />
          <span className="text-xs text-muted-foreground">{goodCount}/{METRICS.length} metrics on track</span>
        </div>
      </div>

      {/* Metrics */}
      <div id="health-metrics-list" className="space-y-2">
        {METRICS.map((metric, i) => (
          <div
            key={metric.label}
            id={`health-metric-${i}`}
            className="flex items-center gap-2.5 py-1.5"
          >
            <StatusIcon status={metric.status} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">{metric.label}</span>
                <span className="text-xs font-semibold text-foreground financial-number">{metric.value}</span>
              </div>
              {metric.detail && (
                <div className="text-[10px] text-muted-foreground/50">{metric.detail}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FinancialHealthScore;
