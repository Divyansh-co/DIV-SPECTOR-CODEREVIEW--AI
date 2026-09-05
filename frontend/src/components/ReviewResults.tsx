import React, { useState, useEffect } from 'react';
import { 
  AlertOctagon, AlertTriangle, Info, Check, 
  FileCode, ShieldCheck, ChevronRight, ChevronDown, 
  Filter, Copy
} from 'lucide-react';
import type { ReviewJobResponse, CodeFinding, Severity, Category } from '../types';

interface ReviewResultsProps {
  reviewData: ReviewJobResponse | null;
}

export const ReviewResults: React.FC<ReviewResultsProps> = ({ reviewData }) => {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [selectedFindingIndex, setSelectedFindingIndex] = useState<number>(0);
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all');
  const [categoryFilter] = useState<Category | 'all'>('all');
  const [expandedDiffs, setExpandedDiffs] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const findings = reviewData?.findings || [];

  // Filtered findings
  const filteredFindings = findings.filter((f) => {
    if (severityFilter !== 'all' && f.severity !== severityFilter) return false;
    if (categoryFilter !== 'all' && f.category !== categoryFilter) return false;
    if (selectedFile && f.file_path !== selectedFile) return false;
    return true;
  });

  // Group findings by file
  const fileGroups = findings.reduce<Record<string, CodeFinding[]>>((acc, f) => {
    if (!acc[f.file_path]) acc[f.file_path] = [];
    acc[f.file_path].push(f);
    return acc;
  }, {});

  const fileList = Object.keys(fileGroups);

  // Keyboard navigation: j / k
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;

      if (e.key === 'j' || e.key === 'ArrowDown') {
        setSelectedFindingIndex((prev) => Math.min(prev + 1, Math.max(0, filteredFindings.length - 1)));
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        setSelectedFindingIndex((prev) => Math.max(prev - 1, 0));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredFindings.length]);

  const toggleDiff = (id: string) => {
    setExpandedDiffs((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopyFix = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!reviewData || findings.length === 0) {
    return (
      <div className="mx-auto max-w-4xl py-12 px-4 text-center">
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-12">
          <FileCode className="mx-auto h-12 w-12 text-fg-muted" />
          <h3 className="mt-4 text-lg font-semibold text-fg-primary">No Findings Available</h3>
          <p className="mt-1 text-sm text-fg-secondary">
            Run a code review to inspect findings with inline annotated diffs and guardrail checks.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl py-6 px-4 space-y-5">
      {/* Top Overview & Metrics Bar */}
      <div className="rounded-xl border border-border-subtle bg-bg-surface p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-fg-primary">
              Review Report: {reviewData.target_name}
            </h2>
            <p className="text-xs text-fg-secondary mt-0.5">
              {reviewData.summary || "Autonomous investigation complete. Findings verified against strict AST and syntax guardrails."}
            </p>
          </div>

          {/* Counts Pills */}
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="flex items-center space-x-1 rounded-md bg-sev-critical/10 border border-sev-critical/30 px-2.5 py-1 text-sev-critical font-medium">
              <AlertOctagon className="h-3.5 w-3.5" />
              <span>{reviewData.critical_count} Critical</span>
            </span>
            <span className="flex items-center space-x-1 rounded-md bg-sev-warning/10 border border-sev-warning/30 px-2.5 py-1 text-sev-warning font-medium">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>{reviewData.warning_count} Warning</span>
            </span>
            <span className="flex items-center space-x-1 rounded-md bg-sev-suggestion/10 border border-sev-suggestion/30 px-2.5 py-1 text-sev-suggestion font-medium">
              <Info className="h-3.5 w-3.5" />
              <span>{reviewData.suggestion_count} Suggestions</span>
            </span>
          </div>
        </div>

        {/* Filter Controls & Keyboard Hint */}
        <div className="mt-4 pt-4 border-t border-border-subtle flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-fg-muted flex items-center gap-1 font-medium">
              <Filter className="h-3.5 w-3.5" /> Filter:
            </span>
            {['all', 'critical', 'warning', 'suggestion'].map((s) => (
              <button
                key={s}
                onClick={() => setSeverityFilter(s as any)}
                className={`rounded px-2.5 py-1 font-mono uppercase text-[11px] transition-colors ${
                  severityFilter === s
                    ? 'bg-accent text-slate-950 font-bold'
                    : 'bg-bg-overlay text-fg-secondary hover:text-fg-primary'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-2 text-fg-muted font-mono text-[11px]">
            <span>Keyboard Shortcuts:</span>
            <kbd className="rounded border border-border-highlight bg-bg-base px-1.5 py-0.5 text-fg-primary font-bold">j</kbd>
            <span>next</span>
            <kbd className="rounded border border-border-highlight bg-bg-base px-1.5 py-0.5 text-fg-primary font-bold">k</kbd>
            <span>prev</span>
          </div>
        </div>
      </div>

      {/* Main PR Review Layout: File Tree (Left) + Finding Details (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: File Explorer Tree */}
        <div className="lg:col-span-4 rounded-xl border border-border-subtle bg-bg-surface p-4 shadow-sm h-fit space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <span className="text-xs font-semibold uppercase tracking-wider text-fg-muted">
              Changed Files ({fileList.length})
            </span>
            {selectedFile && (
              <button
                onClick={() => setSelectedFile(null)}
                className="text-[11px] font-mono text-accent hover:underline"
              >
                Show All Files
              </button>
            )}
          </div>

          <div className="space-y-1 max-h-[500px] overflow-y-auto pr-1">
            {fileList.map((file) => {
              const count = fileGroups[file].length;
              const isSelected = selectedFile === file;
              const hasCritical = fileGroups[file].some(f => f.severity === 'critical');

              return (
                <button
                  key={file}
                  onClick={() => setSelectedFile(isSelected ? null : file)}
                  className={`w-full flex items-center justify-between rounded-lg px-2.5 py-2 text-xs font-mono transition-all text-left ${
                    isSelected
                      ? 'bg-accent/15 border border-accent/40 text-accent font-semibold'
                      : 'hover:bg-bg-overlay text-fg-secondary hover:text-fg-primary'
                  }`}
                >
                  <span className="flex items-center space-x-2 truncate">
                    <FileCode className="h-4 w-4 shrink-0" />
                    <span className="truncate">{file}</span>
                  </span>
                  <span className={`ml-2 rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                    hasCritical 
                      ? 'bg-sev-critical/20 text-sev-critical border border-sev-critical/40' 
                      : 'bg-bg-base text-fg-muted'
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Inline Annotated Findings List */}
        <div className="lg:col-span-8 space-y-4">
          {filteredFindings.map((finding, idx) => {
            const isSelected = idx === selectedFindingIndex;
            const isDiffExpanded = expandedDiffs[finding.id] ?? true;

            const severityBorder = {
              critical: 'border-l-4 border-l-sev-critical border-border-subtle',
              warning: 'border-l-4 border-l-sev-warning border-border-subtle',
              suggestion: 'border-l-4 border-l-sev-suggestion border-border-subtle'
            }[finding.severity];

            const severityBadge = {
              critical: 'bg-sev-critical/10 text-sev-critical border-sev-critical/30',
              warning: 'bg-sev-warning/10 text-sev-warning border-sev-warning/30',
              suggestion: 'bg-sev-suggestion/10 text-sev-suggestion border-sev-suggestion/30'
            }[finding.severity];

            return (
              <div
                key={finding.id}
                onClick={() => setSelectedFindingIndex(idx)}
                className={`rounded-xl border bg-bg-surface p-5 shadow-sm transition-all cursor-pointer ${severityBorder} ${
                  isSelected ? 'ring-1 ring-accent bg-bg-surface/95' : 'hover:border-border-highlight'
                }`}
              >
                {/* Finding Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-border-subtle">
                  <div className="flex items-center space-x-2.5">
                    <span className={`rounded-md border px-2 py-0.5 text-[11px] font-mono font-bold uppercase ${severityBadge}`}>
                      {finding.severity}
                    </span>
                    <span className="rounded-md bg-bg-overlay px-2 py-0.5 text-[11px] font-mono text-fg-secondary border border-border-subtle uppercase">
                      {finding.category}
                    </span>
                    <span className="text-xs font-mono text-fg-muted">
                      Line {finding.line_number}
                    </span>
                  </div>

                  {/* Guardrail Status Badge */}
                  <div className="flex items-center space-x-2">
                    {finding.is_safe_to_apply ? (
                      <span className="flex items-center space-x-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-0.5 text-[10px] font-mono font-medium text-emerald-400">
                        <ShieldCheck className="h-3 w-3" />
                        <span>Safe to Auto-Apply</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-1 rounded-full bg-amber-500/10 border border-amber-500/30 px-2.5 py-0.5 text-[10px] font-mono font-medium text-amber-400">
                        <span>Suggestion Only</span>
                      </span>
                    )}

                    <span className="text-[11px] font-mono text-fg-muted">
                      {Math.round(finding.confidence * 100)}% Confident
                    </span>
                  </div>
                </div>

                {/* File Path */}
                <div className="mt-3 flex items-center text-xs font-mono text-accent">
                  <FileCode className="mr-1.5 h-3.5 w-3.5" />
                  <span>{finding.file_path}:{finding.line_number}</span>
                </div>

                {/* Explanation */}
                <p className="mt-2 text-sm leading-relaxed text-fg-primary">
                  {finding.explanation}
                </p>

                {/* Suggested Fix Diff Box */}
                <div className="mt-4 rounded-lg border border-border-subtle bg-bg-code overflow-hidden">
                  <div className="flex items-center justify-between border-b border-border-subtle bg-bg-base px-3 py-1.5 text-xs font-mono">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleDiff(finding.id);
                      }}
                      className="flex items-center space-x-1 text-fg-secondary hover:text-fg-primary"
                    >
                      {isDiffExpanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                      <span>Suggested Remediation Diff</span>
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyFix(finding.id, finding.suggested_fix);
                      }}
                      className="flex items-center space-x-1 text-fg-muted hover:text-accent transition-colors"
                    >
                      {copiedId === finding.id ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          <span>Copy Fix</span>
                        </>
                      )}
                    </button>
                  </div>

                  {isDiffExpanded && (
                    <div className="p-3 text-xs font-mono overflow-x-auto space-y-1">
                      {finding.original_snippet && (
                        <div className="diff-removed p-1.5 rounded">
                          <span className="text-sev-critical font-bold mr-2">-</span>
                          <code>{finding.original_snippet.trim()}</code>
                        </div>
                      )}
                      <div className="diff-added p-1.5 rounded">
                        <span className="text-emerald-400 font-bold mr-2">+</span>
                        <code>{finding.suggested_fix.trim()}</code>
                      </div>
                    </div>
                  )}
                </div>

              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};
