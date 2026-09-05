import React, { useEffect, useState, useRef } from 'react';
import { 
  Terminal, CheckCircle2, Cpu, 
  ArrowRight, Wrench 
} from 'lucide-react';
import type { ReviewJobResponse } from '../types';

interface LiveProgressProps {
  jobId: string | null;
  onViewResults: () => void;
  reviewData: ReviewJobResponse | null;
}

interface StreamEvent {
  id: string;
  type: string;
  timestamp: string;
  message?: string;
  tool?: string;
  step?: number;
  args?: any;
  duration_ms?: number;
  output_preview?: string;
  status?: string;
  findings_count?: number;
}

export const LiveProgress: React.FC<LiveProgressProps> = ({ jobId, onViewResults, reviewData }) => {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [currentStatus, setCurrentStatus] = useState<string>('Initializing');
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!jobId) return;

    // Connect to backend WebSocket stream
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname || 'localhost';
    const wsUrl = `${protocol}//${host}:8000/ws/review/${jobId}`;
    
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setEvents((prev) => [
          ...prev,
          {
            id: 'init_conn',
            type: 'system',
            timestamp: new Date().toLocaleTimeString(),
            message: `Connected to Specter live telemetry stream for job ${jobId}`
          }
        ]);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const newEvent: StreamEvent = {
            id: `evt_${Date.now()}_${Math.random()}`,
            type: data.type,
            timestamp: new Date().toLocaleTimeString(),
            ...data
          };

          setEvents((prev) => [...prev, newEvent]);

          if (data.type === 'status_update') {
            setCurrentStatus(data.message || data.status);
          } else if (data.type === 'completed') {
            setIsCompleted(true);
            setCurrentStatus('Review Finished');
          }
        } catch (e) {
          console.error("WS Parse error", e);
        }
      };

      ws.onerror = () => {
        setCurrentStatus('Telemetry active (polling mode)');
      };
    } catch (e) {
      console.warn("WebSocket init error", e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [jobId]);

  // Auto-scroll terminal
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [events]);

  // If review is completed already from props
  useEffect(() => {
    if (reviewData?.status === 'completed') {
      setIsCompleted(true);
      setCurrentStatus('Review Completed');
    }
  }, [reviewData]);

  if (!jobId) {
    return (
      <div className="mx-auto max-w-4xl py-12 px-4 text-center">
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-12">
          <Terminal className="mx-auto h-12 w-12 text-fg-muted" />
          <h3 className="mt-4 text-lg font-semibold text-fg-primary">No Active Review Running</h3>
          <p className="mt-1 text-sm text-fg-secondary">
            Submit a codebase scan or diff from the "Submit Review" tab to watch real-time tool execution.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl py-6 px-4 space-y-6">
      {/* Live Header Status */}
      <div className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <span className={`h-2.5 w-2.5 rounded-full ${isCompleted ? 'bg-emerald-400' : 'bg-accent animate-ping'}`} />
            <h2 className="text-xl font-bold tracking-tight text-fg-primary">
              {isCompleted ? 'Investigation Concluded' : 'Autonomous Agent Investigating'}
            </h2>
          </div>
          <div className="mt-1 flex items-center space-x-3 text-xs font-mono text-fg-muted">
            <span>JOB: <strong className="text-fg-secondary">{jobId}</strong></span>
            <span>•</span>
            <span>PHASE: <strong className="text-accent">{currentStatus}</strong></span>
          </div>
        </div>

        {isCompleted && (
          <button
            onClick={onViewResults}
            className="flex items-center space-x-2 rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-accent-hover transition-colors shadow-md"
          >
            <span>Inspect Findings ({reviewData?.findings_count || 0})</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Styled Terminal Output */}
      <div className="rounded-xl border border-border-subtle bg-bg-code shadow-md overflow-hidden">
        {/* Terminal Titlebar */}
        <div className="flex items-center justify-between border-b border-border-subtle bg-bg-base px-4 py-2.5">
          <div className="flex items-center space-x-2">
            <div className="h-3 w-3 rounded-full bg-rose-500/80" />
            <div className="h-3 w-3 rounded-full bg-amber-500/80" />
            <div className="h-3 w-3 rounded-full bg-emerald-500/80" />
            <span className="ml-2 text-xs font-mono text-fg-muted">specter-agent-daemon // live-trace</span>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-fg-muted">
            <Cpu className="h-3.5 w-3.5 text-accent" />
            <span>Divyansh Mishra Engine</span>
          </div>
        </div>

        {/* Console Event Stream */}
        <div 
          ref={logContainerRef}
          className="h-[460px] overflow-y-auto p-4 font-mono text-xs space-y-2.5"
        >
          {events.length === 0 && (
            <div className="flex items-center space-x-2 text-fg-muted py-4">
              <span className="h-2 w-2 rounded-full bg-accent animate-ping" />
              <span>Awaiting agent trace stream from backend WebSocket...</span>
            </div>
          )}

          {events.map((evt) => {
            if (evt.type === 'trace_start') {
              return (
                <div key={evt.id} className="rounded border border-accent/20 bg-accent/5 p-2.5 animate-fadeIn">
                  <div className="flex items-center justify-between text-accent font-semibold">
                    <span className="flex items-center space-x-1.5">
                      <Wrench className="h-3.5 w-3.5" />
                      <span>[STEP {evt.step}] Invoking Tool: {evt.tool}</span>
                    </span>
                    <span className="text-[10px] text-fg-muted">{evt.timestamp}</span>
                  </div>
                  <div className="mt-1 text-fg-secondary">
                    <span className="text-fg-muted">Args:</span> {JSON.stringify(evt.args)}
                  </div>
                </div>
              );
            }

            if (evt.type === 'trace_end') {
              return (
                <div key={evt.id} className="rounded border border-border-subtle bg-bg-surface p-2.5 ml-4">
                  <div className="flex items-center justify-between text-fg-secondary">
                    <span className="flex items-center space-x-1.5 text-emerald-400">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>Completed {evt.tool} ({evt.duration_ms}ms)</span>
                    </span>
                    <span className="text-[10px] text-fg-muted">{evt.timestamp}</span>
                  </div>
                  {evt.output_preview && (
                    <div className="mt-1 text-fg-muted text-[11px] truncate">
                      Output: {evt.output_preview}
                    </div>
                  )}
                </div>
              );
            }

            if (evt.type === 'completed') {
              return (
                <div key={evt.id} className="rounded border border-emerald-500/30 bg-emerald-500/10 p-3 text-emerald-400">
                  <div className="font-semibold flex items-center space-x-2">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Review Completed! Discovered {evt.findings_count || 0} actionable findings.</span>
                  </div>
                </div>
              );
            }

            return (
              <div key={evt.id} className="flex items-start space-x-2 text-fg-secondary">
                <span className="text-fg-muted">[{evt.timestamp}]</span>
                <span>{evt.message || JSON.stringify(evt)}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
