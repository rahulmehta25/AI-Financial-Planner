import React, { useEffect, useRef } from "react";
import { Target, Home, GraduationCap, Plane, Landmark } from "lucide-react";

interface Goal {
  name: string;
  icon: React.ElementType;
  currentAmount: number;
  targetAmount: number;
  progress: number;
  color: string;
  glowColor: string;
  deadline?: string;
}

const GOALS: Goal[] = [
  { name: "Retirement",     icon: Landmark,      currentAmount: 285000, targetAmount: 1200000, progress: 24, color: "#1a7dff", glowColor: "rgba(26,125,255,0.4)", deadline: "2048" },
  { name: "House Down",     icon: Home,          currentAmount: 48500,  targetAmount: 80000,   progress: 61, color: "#f9b820", glowColor: "rgba(249,184,32,0.4)",  deadline: "2026" },
  { name: "Emergency Fund", icon: Target,        currentAmount: 22000,  targetAmount: 30000,   progress: 73, color: "#10d077", glowColor: "rgba(16,208,119,0.4)",  deadline: "2025" },
  { name: "Education",      icon: GraduationCap, currentAmount: 8200,   targetAmount: 50000,   progress: 16, color: "#7c3aed", glowColor: "rgba(124,58,237,0.4)",  deadline: "2030" },
  { name: "Travel Fund",    icon: Plane,         currentAmount: 3800,   targetAmount: 10000,   progress: 38, color: "#06b6d4", glowColor: "rgba(6,182,212,0.4)",   deadline: "2025" },
];

const formatCurrency = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }).format(v);

interface RingProps {
  progress: number;
  size: number;
  strokeWidth: number;
  color: string;
  glowColor: string;
  id: string;
}

const Ring: React.FC<RingProps> = ({ progress, size, strokeWidth, color, glowColor, id }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <svg
      id={id}
      width={size}
      height={size}
      className="goal-ring"
      style={{ filter: `drop-shadow(0 0 6px ${glowColor})` }}
    >
      {/* Track */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="hsl(220 38% 14%)"
        strokeWidth={strokeWidth}
      />
      {/* Progress */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{
          transition: "stroke-dashoffset 1.4s cubic-bezier(0.34, 1.56, 0.64, 1)",
        }}
      />
    </svg>
  );
};

const GoalProgressRings: React.FC<{ goals?: Goal[] }> = ({ goals = GOALS }) => {
  return (
    <div id="goal-progress-card" className="metric-card metric-card-green">
      <div id="goal-progress-header" className="flex items-center justify-between mb-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Financial Goals</p>
          <h3 className="text-lg font-bold text-foreground">Progress Tracker</h3>
        </div>
        <span className="badge-gold">{goals.filter(g => g.progress >= 75).length} On Track</span>
      </div>

      <div id="goal-progress-list" className="space-y-4">
        {goals.map((goal, i) => {
          const Icon = goal.icon;
          const remaining = goal.targetAmount - goal.currentAmount;
          return (
            <div
              key={goal.name}
              id={`goal-item-${i}`}
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/[0.03] transition-colors group"
            >
              {/* Ring */}
              <div id={`goal-ring-${i}`} className="relative flex-shrink-0">
                <Ring
                  progress={goal.progress}
                  size={52}
                  strokeWidth={4}
                  color={goal.color}
                  glowColor={goal.glowColor}
                  id={`ring-svg-${i}`}
                />
                {/* Icon in center */}
                <div
                  id={`goal-icon-${i}`}
                  className="absolute inset-0 flex items-center justify-center"
                >
                  <Icon className="w-4 h-4" style={{ color: goal.color }} />
                </div>
              </div>

              {/* Info */}
              <div id={`goal-info-${i}`} className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-foreground truncate">{goal.name}</span>
                  <span className="text-sm font-bold ml-2 financial-number" style={{ color: goal.color }}>
                    {goal.progress}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="financial-number">{formatCurrency(goal.currentAmount)}</span>
                  <span className="financial-number text-muted-foreground/60">/ {formatCurrency(goal.targetAmount)}</span>
                </div>
                {goal.deadline && (
                  <div className="text-[10px] text-muted-foreground/50 mt-0.5">Target: {goal.deadline}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GoalProgressRings;
