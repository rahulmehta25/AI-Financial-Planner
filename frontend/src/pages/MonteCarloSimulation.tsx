import React, { useState, useCallback, useEffect } from "react";
import { toast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Play,
  Download,
  GitCompare,
  AlertTriangle,
  CheckCircle,
  Info,
  TrendingUp,
  Calculator,
  BarChart3,
  Zap,
  Target,
  Shield,
  Activity,
} from "lucide-react";

import SimulationControls, { SimulationParameters } from "@/components/simulation/SimulationControls";
import SimulationResults from "@/components/simulation/SimulationResults";
import ProbabilityChart, { SimulationResult } from "@/components/simulation/ProbabilityChart";
import { monteCarloService, MonteCarloRequest, MonteCarloResponse, ScenarioComparison } from "@/services/monteCarlo";

/* ─── Formatters ─── */
const fmt = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);
const fmtK = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 }).format(v);

/* ─── Metric card for results ─── */
const ResultMetric: React.FC<{ label: string; value: string; sub?: string; color?: string; icon?: React.ElementType }> = ({
  label, value, sub, color = "text-foreground", icon: Icon,
}) => (
  <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] space-y-1">
    {Icon && <Icon className={`w-4 h-4 mb-1 ${color}`} />}
    <div className={`text-lg font-bold financial-number ${color}`}>{value}</div>
    <div className="text-xs text-muted-foreground">{label}</div>
    {sub && <div className="text-[10px] text-muted-foreground/60">{sub}</div>}
  </div>
);

/* ─── Preset buttons ─── */
const PRESETS = [
  { key: "stocks",     label: "Stocks",     desc: "High growth",      color: "blue"   },
  { key: "bonds",      label: "Bonds",      desc: "Stable income",    color: "emerald"},
  { key: "mixed",      label: "Balanced",   desc: "60/40 mix",        color: "gold"   },
  { key: "aggressive", label: "Aggressive", desc: "Max growth",       color: "violet" },
];

const PRESET_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  blue:   { bg: "bg-blue-500/8",   border: "border-blue-500/20",   text: "text-blue-300"   },
  emerald:{ bg: "bg-emerald-500/8",border: "border-emerald-500/20",text: "text-emerald-300"},
  gold:   { bg: "bg-amber-500/8",  border: "border-amber-500/20",  text: "text-amber-300"  },
  violet: { bg: "bg-violet-500/8", border: "border-violet-500/20", text: "text-violet-300" },
};

/* ─── Main ─── */
const MonteCarloSimulation: React.FC = () => {
  const [parameters, setParameters] = useState<SimulationParameters>({
    timeHorizon: 30,
    initialInvestment: 100000,
    monthlyContribution: 1000,
    expectedReturn: 0.08,
    volatility: 0.15,
    riskFreeRate: 0.02,
    numSimulations: 10000,
    jumpIntensity: 0.1,
    jumpSizeMean: -0.05,
    jumpSizeStd: 0.2,
    enableRegimeSwitching: false,
    regimeDetection: false,
    targetAmount: undefined,
    successThreshold: 0.95,
  });

  const [isRunning, setIsRunning]           = useState(false);
  const [simulationId, setSimulationId]     = useState<string | null>(null);
  const [progress, setProgress]             = useState(0);
  const [results, setResults]               = useState<SimulationResult | null>(null);
  const [error, setError]                   = useState<string | null>(null);
  const [warnings, setWarnings]             = useState<string[]>([]);
  const [scenarios, setScenarios]           = useState<Array<{ name: string; parameters: SimulationParameters; results?: SimulationResult }>>([]);

  useEffect(() => {
    const v = monteCarloService.validateParameters(parameters);
    setWarnings(v.warnings);
    setError(v.isValid ? null : v.errors.join(", "));
  }, [parameters]);

  const transformResults = useCallback((r: MonteCarloResponse): SimulationResult => ({
    finalValues: r.final_values,
    paths: r.paths,
    timestamps: r.timestamps,
    riskMetrics: r.risk_metrics,
    successRate: parameters.targetAmount
      ? r.final_values.filter(v => v >= parameters.targetAmount!).length / r.final_values.length
      : undefined,
    confidenceIntervals: r.confidence_intervals,
  }), [parameters.targetAmount]);

  const handleRun = useCallback(async () => {
    try {
      setIsRunning(true); setError(null); setProgress(0);
      const v = monteCarloService.validateParameters(parameters);
      if (!v.isValid) throw new Error(v.errors.join(", "));

      const progressInterval = setInterval(() => {
        setProgress(prev => (prev >= 90 ? prev : prev + Math.random() * 12));
      }, 400);

      toast({ title: "Simulation Started", description: `Running ${parameters.numSimulations.toLocaleString()} paths…` });

      const response = await monteCarloService.runSimulation(parameters as MonteCarloRequest);
      clearInterval(progressInterval);
      setProgress(100);
      setResults(transformResults(response));
      setSimulationId(response.simulation_id);
      toast({ title: "Complete", description: `Finished in ${response.metadata.computation_time.toFixed(2)}s` });
    } catch (err: any) {
      setError(err.message);
      toast({ title: "Simulation Failed", description: err.message, variant: "destructive" });
    } finally {
      setIsRunning(false);
    }
  }, [parameters, transformResults]);

  const handleExport = useCallback(async () => {
    if (!simulationId) return;
    try {
      const blob = await monteCarloService.exportResults(simulationId, "csv");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `mc-${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(url);
      toast({ title: "Exported", description: "Results downloaded as CSV." });
    } catch (err: any) {
      toast({ title: "Export Failed", description: err.message, variant: "destructive" });
    }
  }, [simulationId]);

  const handlePreset = useCallback((key: string) => {
    const suggested = monteCarloService.getSuggestedParameters(key as any);
    setParameters(prev => ({ ...prev, ...suggested }));
    toast({ title: "Preset Loaded", description: `Loaded ${key} parameters.` });
  }, []);

  const handleAddScenario = useCallback(() => {
    if (!results) return;
    setScenarios(prev => [...prev, { name: `Scenario ${prev.length + 1}`, parameters: { ...parameters }, results }]);
    toast({ title: "Scenario Added", description: `Scenario ${scenarios.length + 1} added to comparison.` });
  }, [results, parameters, scenarios.length]);

  /* Derived summary stats */
  const meanValue    = results ? results.finalValues.reduce((a, b) => a + b, 0) / results.finalValues.length : 0;
  const medianValue  = results ? results.finalValues.sort((a, b) => a - b)[Math.floor(results.finalValues.length * 0.5)] : 0;
  const worstCase    = results ? results.finalValues[Math.floor(results.finalValues.length * 0.05)] : 0;
  const bestCase     = results ? results.finalValues[Math.floor(results.finalValues.length * 0.95)] : 0;

  return (
    <div id="monte-carlo-page" className="page-enter pt-4 space-y-5 pb-10">

      {/* ─── Header ─── */}
      <div id="mc-header" className="flex items-start justify-between">
        <div id="mc-title-group">
          <div className="flex items-center gap-2.5 mb-1">
            <div className="w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/25 flex items-center justify-center">
              <Calculator className="w-4 h-4 text-blue-400" />
            </div>
            <h1 id="mc-title" className="text-xl font-bold text-foreground">Monte Carlo Simulation</h1>
            <Badge variant="outline" className="bg-blue-500/10 border-blue-500/25 text-blue-300 text-[10px]">
              Browser-Native
            </Badge>
          </div>
          <p id="mc-subtitle" className="text-sm text-muted-foreground">
            Statistical portfolio simulation with geometric Brownian motion & jump-diffusion modeling
          </p>
        </div>

        <div id="mc-header-actions" className="flex items-center gap-2">
          {/* Presets */}
          <div id="mc-presets" className="flex gap-1.5">
            {PRESETS.map(p => {
              const c = PRESET_COLORS[p.color];
              return (
                <button
                  key={p.key}
                  id={`preset-${p.key}`}
                  onClick={() => handlePreset(p.key)}
                  className={`px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all hover:opacity-90 ${c.bg} ${c.border} ${c.text}`}
                >
                  {p.label}
                </button>
              );
            })}
          </div>

          {results && (
            <>
              <Button variant="outline" size="sm" onClick={handleAddScenario}
                className="h-8 px-3 text-xs border-white/10 hover:bg-white/[0.04] gap-1.5">
                <GitCompare className="w-3.5 h-3.5" /> Save Scenario
              </Button>
              <Button variant="outline" size="sm" onClick={handleExport}
                className="h-8 px-3 text-xs border-white/10 hover:bg-white/[0.04] gap-1.5">
                <Download className="w-3.5 h-3.5" /> Export CSV
              </Button>
            </>
          )}
        </div>
      </div>

      {/* ─── Alerts ─── */}
      {(error || warnings.length > 0) && (
        <div id="mc-alerts" className="space-y-2">
          {error && (
            <Alert variant="destructive" id="mc-error" className="glass border-red-500/30 bg-red-500/5">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {warnings.map((w, i) => (
            <Alert key={i} id={`mc-warning-${i}`} className="glass border-amber-500/30 bg-amber-500/5">
              <Info className="h-4 w-4 text-amber-400" />
              <AlertDescription className="text-amber-300">{w}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}

      {/* ─── Progress ─── */}
      {isRunning && (
        <div id="mc-progress-bar" className="glass-card rounded-2xl p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400 animate-pulse" />
              <span className="text-sm font-medium text-foreground">Running {parameters.numSimulations.toLocaleString()} simulations…</span>
            </div>
            <Badge variant="outline" className="bg-blue-500/10 border-blue-500/25 text-blue-300 text-xs">
              {progress.toFixed(0)}%
            </Badge>
          </div>
          <Progress value={progress} className="h-1.5" />
        </div>
      )}

      {/* ─── Main two-column layout ─── */}
      <div id="mc-main-layout" className="grid grid-cols-1 xl:grid-cols-[340px_1fr] gap-5">

        {/* Controls */}
        <div id="mc-controls-col">
          <div className="glass-card rounded-2xl overflow-hidden sticky top-5">
            <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-semibold text-foreground">Parameters</span>
              </div>
              <Button
                id="mc-run-btn"
                size="sm"
                onClick={handleRun}
                disabled={isRunning || !!error}
                className="h-8 px-4 text-xs gap-1.5 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white border-0 shadow-glow-blue disabled:opacity-50"
              >
                {isRunning ? (
                  <><Activity className="w-3.5 h-3.5 animate-spin" /> Running…</>
                ) : (
                  <><Play className="w-3.5 h-3.5" /> Run Simulation</>
                )}
              </Button>
            </div>
            <div className="p-4">
              <SimulationControls
                parameters={parameters}
                onParametersChange={setParameters}
                onRunSimulation={handleRun}
                isRunning={isRunning}
              />
            </div>
          </div>
        </div>

        {/* Results */}
        <div id="mc-results-col" className="space-y-5">

          {/* Summary metrics */}
          {results ? (
            <>
              <div id="mc-summary-metrics" className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <ResultMetric label="Expected Value"    value={fmtK(meanValue)}   icon={TrendingUp} color="text-blue-300"   />
                <ResultMetric label="Median Outcome"    value={fmtK(medianValue)} icon={BarChart3}  color="text-foreground"  />
                <ResultMetric label="5th Percentile"    value={fmtK(worstCase)}   icon={Shield}     color="text-red-400"     sub="Bear case" />
                <ResultMetric
                  label={results.successRate != null ? "Success Rate" : "95th Pctile"}
                  value={results.successRate != null ? `${(results.successRate * 100).toFixed(1)}%` : fmtK(bestCase)}
                  icon={Target}
                  color={results.successRate != null && results.successRate >= 0.7 ? "text-positive" : "text-amber-300"}
                />
              </div>

              {/* Risk metrics row */}
              <div id="mc-risk-metrics" className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(results.riskMetrics).slice(0, 6).map(([key, val], i) => (
                  <div key={key} id={`risk-metric-${i}`} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                    <div className="text-xs text-muted-foreground mb-1">{key}</div>
                    <div className="text-sm font-bold financial-number text-foreground">
                      {typeof val === "number"
                        ? key.toLowerCase().includes("ratio") || key.toLowerCase().includes("beta") || key.toLowerCase().includes("skew") || key.toLowerCase().includes("kurt")
                          ? val.toFixed(2)
                          : fmt(val)
                        : val}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            /* Empty state */
            <div id="mc-empty-state" className="glass-card rounded-2xl p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4">
                <Calculator className="w-8 h-8 text-blue-400" />
              </div>
              <h3 className="text-base font-semibold text-foreground mb-2">Ready to Simulate</h3>
              <p className="text-sm text-muted-foreground max-w-sm mb-5">
                Configure your parameters in the left panel, choose a preset, then click Run Simulation to generate your Monte Carlo analysis.
              </p>
              <div id="mc-empty-presets" className="flex gap-2 flex-wrap justify-center">
                {PRESETS.map(p => {
                  const c = PRESET_COLORS[p.color];
                  return (
                    <button key={p.key} id={`empty-preset-${p.key}`} onClick={() => handlePreset(p.key)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${c.bg} ${c.border} ${c.text} transition-all hover:opacity-90`}>
                      {p.label} — {p.desc}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Confidence band chart */}
          {results && (
            <div id="mc-confidence-chart" className="glass-card rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Percentile Fan Chart</h3>
                  <p className="text-xs text-muted-foreground">Distribution of outcomes across all simulations</p>
                </div>
                <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                  {[
                    { label: "90th pct", color: "hsl(214 100% 57% / 0.15)" },
                    { label: "Median",   color: "hsl(43 96% 54%)" },
                    { label: "10th pct", color: "hsl(214 100% 57% / 0.45)" },
                  ].map(l => (
                    <div key={l.label} className="flex items-center gap-1">
                      <div className="w-2 h-2 rounded-sm" style={{ background: l.color }} />
                      {l.label}
                    </div>
                  ))}
                </div>
              </div>
              <SimulationResults
                results={results}
                targetAmount={parameters.targetAmount}
                onExportResults={simulationId ? handleExport : undefined}
              />
            </div>
          )}

          {/* Probability chart */}
          {results && (
            <div id="mc-probability-chart" className="glass-card rounded-2xl p-5">
              <h3 className="text-sm font-semibold text-foreground mb-4">Outcome Probability Distribution</h3>
              <ProbabilityChart results={results} targetAmount={parameters.targetAmount} />
            </div>
          )}
        </div>
      </div>

      {/* ─── Scenario comparison ─── */}
      {scenarios.length > 0 && (
        <>
          <Separator className="border-white/[0.06]" />
          <div id="mc-scenarios" className="glass-card rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <GitCompare className="w-4 h-4 text-blue-400" />
              <h3 className="text-sm font-semibold text-foreground">Scenario Comparison</h3>
              <Badge variant="outline" className="bg-blue-500/10 border-blue-500/20 text-blue-300 text-[10px] ml-auto">
                {scenarios.length} saved
              </Badge>
            </div>
            <div id="scenarios-grid" className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {scenarios.map((sc, i) => (
                <div key={i} id={`scenario-${i}`} className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-foreground">{sc.name}</span>
                    <button
                      id={`remove-scenario-${i}`}
                      onClick={() => setScenarios(prev => prev.filter((_, idx) => idx !== i))}
                      className="text-[10px] text-muted-foreground hover:text-red-400 transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between"><span className="text-muted-foreground">Initial</span><span className="font-medium financial-number">{fmt(sc.parameters.initialInvestment)}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Return</span><span className="font-medium">{(sc.parameters.expectedReturn * 100).toFixed(1)}%</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Volatility</span><span className="font-medium">{(sc.parameters.volatility * 100).toFixed(1)}%</span></div>
                    {sc.results && (
                      <>
                        <Separator className="border-white/[0.06] my-1.5" />
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Expected</span>
                          <span className="font-bold text-positive financial-number">
                            {fmtK(sc.results.finalValues.reduce((a, b) => a + b, 0) / sc.results.finalValues.length)}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MonteCarloSimulation;
