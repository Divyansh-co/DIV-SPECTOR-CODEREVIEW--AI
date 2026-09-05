import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid 
} from 'recharts';
import { 
  BarChart3, CheckCircle2, XCircle, RotateCcw, 
  Award, Shield, Target, Cpu 
} from 'lucide-react';
import type { BenchmarkEvaluationReport } from '../types';

interface EvalDashboardProps {
  evaluation: BenchmarkEvaluationReport | null;
  onRerun: () => void;
  isLoading: boolean;
}

export const EvalDashboard: React.FC<EvalDashboardProps> = ({ evaluation, onRerun, isLoading }) => {
  if (!evaluation) {
    return (
      <div className="mx-auto max-w-4xl py-12 px-4 text-center">
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-12">
          <BarChart3 className="mx-auto h-12 w-12 text-fg-muted" />
          <h3 className="mt-4 text-lg font-semibold text-fg-primary">Benchmark Suite Loading</h3>
          <p className="mt-1 text-sm text-fg-secondary">
            Fetching precision, recall, and F1 performance benchmarks...
          </p>
        </div>
      </div>
    );
  }

  // Format data for Recharts
  const chartData = Object.entries(evaluation.category_metrics || {}).map(([category, stats]) => ({
    category: category.toUpperCase(),
    Precision: Math.round(stats.precision * 100),
    Recall: Math.round(stats.recall * 100),
    F1: Math.round(stats.f1_score * 100)
  }));

  return (
    <div className="mx-auto max-w-6xl py-6 px-4 space-y-6">
      {/* Top Banner with Re-run Button */}
      <div className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1 text-xs font-mono text-accent">
            <Award className="h-3.5 w-3.5" />
            <span>Standardized Empirical Benchmark Evaluation Suite</span>
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-fg-primary">
            Defect Detection Accuracy & Evaluation
          </h1>
          <p className="mt-1 text-sm text-fg-secondary">
            Ground-truth labeled test suite of 12 real-world defect patterns including SQLi, Off-by-one, Null Dereference, ReDoS, and clean control validation.
          </p>
        </div>

        <button
          onClick={onRerun}
          disabled={isLoading}
          className="flex items-center space-x-2 rounded-lg border border-border-highlight bg-bg-overlay px-4 py-2.5 text-xs font-mono font-semibold text-fg-primary hover:border-accent hover:text-accent transition-all disabled:opacity-50"
        >
          <RotateCcw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>{isLoading ? 'Running Suite...' : 'Re-Run Evaluation Suite'}</span>
        </button>
      </div>

      {/* Primary KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Precision */}
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-fg-muted font-mono">
              PRECISION
            </span>
            <Target className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-emerald-400 font-mono">
              {(evaluation.precision * 100).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-[11px] text-fg-muted">
            TP / (TP + FP) — Zero hallucinated defects on clean control code
          </p>
        </div>

        {/* Recall */}
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-fg-muted font-mono">
              RECALL
            </span>
            <Shield className="h-4 w-4 text-accent" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-accent font-mono">
              {(evaluation.recall * 100).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-[11px] text-fg-muted">
            TP / (TP + FN) — Ratio of real vulnerabilities identified
          </p>
        </div>

        {/* F1 Score */}
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-fg-muted font-mono">
              F1 SCORE
            </span>
            <Award className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-amber-400 font-mono">
              {(evaluation.f1_score * 100).toFixed(1)}%
            </span>
          </div>
          <p className="mt-1 text-[11px] text-fg-muted">
            Harmonic mean of precision & recall
          </p>
        </div>

        {/* Total Cases */}
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-fg-muted font-mono">
              BENCHMARK SUITE
            </span>
            <Cpu className="h-4 w-4 text-purple-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-3xl font-extrabold text-fg-primary font-mono">
              {evaluation.total_cases}
            </span>
            <span className="text-xs text-fg-muted font-mono">CASES</span>
          </div>
          <p className="mt-1 text-[11px] text-fg-muted">
            {evaluation.true_positives} Detected • {evaluation.false_positives} FP
          </p>
        </div>
      </div>

      {/* Recharts Category Comparison Chart */}
      <div className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-fg-primary">
              Accuracy Metrics Across Bug Categories
            </h3>
            <p className="text-xs text-fg-muted">
              Comparison of Precision, Recall, and F1 Score for Security, Logic Bugs, Performance, and Maintainability.
            </p>
          </div>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="category" stroke="#94a3b8" fontSize={12} fontFamily="JetBrains Mono" />
              <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} fontFamily="JetBrains Mono" unit="%" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#0f172a', 
                  borderColor: '#334155', 
                  borderRadius: '8px',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px'
                }} 
              />
              <Legend wrapperStyle={{ fontFamily: 'JetBrains Mono', fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="Precision" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Recall" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              <Bar dataKey="F1" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Benchmark Test Cases Table */}
      <div className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-fg-primary mb-4">
          Empirical Benchmark Test Cases & Ground Truth Audits
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-border-subtle font-mono uppercase text-fg-muted">
              <tr>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Benchmark Case</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Target Line</th>
                <th className="py-2.5 px-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50 font-mono">
              {evaluation.cases.map((c) => {
                const isPass = c.status.startsWith('PASS');

                return (
                  <tr key={c.case_id} className="hover:bg-bg-overlay/50 transition-colors">
                    <td className="py-2.5 px-3">
                      {isPass ? (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>PASS</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-rose-500/10 border border-rose-500/30 px-2 py-0.5 text-[10px] font-bold text-rose-400">
                          <XCircle className="h-3 w-3" />
                          <span>FAIL</span>
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-fg-primary">
                      {c.title}
                    </td>
                    <td className="py-2.5 px-3 uppercase text-fg-secondary">
                      {c.category}
                    </td>
                    <td className="py-2.5 px-3 text-fg-muted">
                      {c.expected_line > 0 ? `L${c.expected_line}` : 'Control (0)'}
                    </td>
                    <td className="py-2.5 px-3 font-sans text-fg-secondary text-xs max-w-md truncate">
                      {c.description}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
