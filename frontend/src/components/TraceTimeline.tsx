import React, { useState } from 'react';
import { 
  Activity, ChevronDown, ChevronRight, 
  Terminal, Search, FileText, Wrench 
} from 'lucide-react';
import type { AgentToolTrace } from '../types';

interface TraceTimelineProps {
  traces: AgentToolTrace[];
  jobId: string | null;
}

export const TraceTimeline: React.FC<TraceTimelineProps> = ({ traces }) => {
  const [expandedTrace, setExpandedTrace] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedTrace((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (!traces || traces.length === 0) {
    return (
      <div className="mx-auto max-w-4xl py-12 px-4 text-center">
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-12">
          <Activity className="mx-auto h-12 w-12 text-fg-muted" />
          <h3 className="mt-4 text-lg font-semibold text-fg-primary">No Agent Traces Available</h3>
          <p className="mt-1 text-sm text-fg-secondary">
            Execute a review to record and analyze the agent's multi-turn tool calling waterfall.
          </p>
        </div>
      </div>
    );
  }

  const totalDuration = traces.reduce((acc, t) => acc + (t.duration_ms || 0), 0);

  return (
    <div className="mx-auto max-w-5xl py-6 px-4 space-y-6">
      {/* Header Stat Cards */}
      <div className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-fg-primary">
              Agent Observability & Reasoning Trace
            </h2>
            <p className="text-xs text-fg-secondary mt-0.5">
              Detailed breakdown of autonomous tool calls, reasoning hypotheses, execution latency, and raw I/O.
            </p>
          </div>

          <div className="flex items-center space-x-3 text-xs font-mono">
            <div className="rounded-lg border border-border-subtle bg-bg-base px-3 py-2">
              <span className="text-fg-muted block text-[10px]">TOTAL TOOL STEPS</span>
              <span className="text-accent font-bold text-sm">{traces.length}</span>
            </div>
            <div className="rounded-lg border border-border-subtle bg-bg-base px-3 py-2">
              <span className="text-fg-muted block text-[10px]">TOTAL TOOL LATENCY</span>
              <span className="text-emerald-400 font-bold text-sm">{totalDuration}ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* Waterfall Timeline List */}
      <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-border-subtle">
        {traces.map((trace, idx) => {
          const isExpanded = expandedTrace[trace.id] ?? (idx === 0);

          const toolIcon = {
            search_codebase: Search,
            read_file: FileText,
            run_linter: Wrench,
            run_tests: Terminal,
            get_function_callers: Activity
          }[trace.tool_name] || Activity;

          const IconComponent = toolIcon;

          return (
            <div key={trace.id} className="relative group">
              {/* Timeline Pip */}
              <div className="absolute -left-[30px] top-4 flex h-6 w-6 items-center justify-center rounded-full border border-border-subtle bg-bg-surface group-hover:border-accent group-hover:text-accent transition-colors">
                <span className="font-mono text-[10px] font-bold text-fg-muted group-hover:text-accent">
                  {trace.step_number}
                </span>
              </div>

              {/* Step Card */}
              <div className="rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-sm hover:border-border-highlight transition-colors">
                {/* Header */}
                <div 
                  onClick={() => toggleExpand(trace.id)}
                  className="flex flex-wrap items-center justify-between gap-2 cursor-pointer select-none"
                >
                  <div className="flex items-center space-x-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-md bg-accent/10 text-accent">
                      <IconComponent className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-mono font-semibold text-xs text-fg-primary">
                        {trace.tool_name}
                      </span>
                      <span className="ml-2 font-mono text-[10px] text-fg-muted">
                        {trace.timestamp}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 font-mono text-[10px] text-emerald-400">
                      {trace.duration_ms}ms
                    </span>
                    {isExpanded ? <ChevronDown className="h-4 w-4 text-fg-muted" /> : <ChevronRight className="h-4 w-4 text-fg-muted" />}
                  </div>
                </div>

                {/* Thought hypothesis if available */}
                {trace.thought && (
                  <div className="mt-3 rounded-md bg-bg-base/70 p-2.5 text-xs text-fg-secondary border border-border-subtle/50">
                    <span className="font-semibold text-accent block text-[11px] mb-1 font-mono">Agent Hypothesis / Intent:</span>
                    {trace.thought}
                  </div>
                )}

                {/* Expanded Details: Arguments & Raw Output */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t border-border-subtle space-y-3 font-mono text-xs">
                    {/* Tool Input */}
                    <div>
                      <span className="text-[11px] uppercase tracking-wider text-fg-muted block mb-1">
                        Input Parameters
                      </span>
                      <pre className="rounded-lg bg-bg-code p-2.5 text-fg-secondary overflow-x-auto border border-border-subtle">
                        {JSON.stringify(trace.tool_input, null, 2)}
                      </pre>
                    </div>

                    {/* Tool Output */}
                    <div>
                      <span className="text-[11px] uppercase tracking-wider text-fg-muted block mb-1">
                        Tool Execution Output
                      </span>
                      <pre className="rounded-lg bg-bg-code p-2.5 text-fg-secondary overflow-x-auto max-h-56 border border-border-subtle">
                        {trace.tool_output}
                      </pre>
                    </div>
                  </div>
                )}

              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
