import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { WatermarkOverlay } from './components/WatermarkOverlay';
import { SubmitReview } from './components/SubmitReview';
import { LiveProgress } from './components/LiveProgress';
import { ReviewResults } from './components/ReviewResults';
import { TraceTimeline } from './components/TraceTimeline';
import { EvalDashboard } from './components/EvalDashboard';
import { Toast } from './components/Toast';
import type { ToastMessage } from './components/Toast';
import type { ReviewSubmitPayload, ReviewJobResponse, BenchmarkEvaluationReport } from './types';

const API_BASE = 'http://localhost:8000';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('submit');
  const [isDark, setIsDark] = useState<boolean>(true);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [reviewData, setReviewData] = useState<ReviewJobResponse | null>(null);
  const [evaluation, setEvaluation] = useState<BenchmarkEvaluationReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isEvalLoading, setIsEvalLoading] = useState<boolean>(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const pollTimerRef = useRef<any>(null);

  // Apply dark mode class to document
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
    }
  }, [isDark]);

  // Load benchmark evaluation on initial mount
  useEffect(() => {
    fetchEvaluation();
  }, []);

  const fetchEvaluation = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/evaluation`);
      if (res.ok) {
        const data = await res.json();
        setEvaluation(data);
      }
    } catch (err) {
      console.warn("Could not fetch evaluation", err);
    }
  };

  const handleRerunEvaluation = async () => {
    setIsEvalLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/evaluation/run`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setEvaluation(data);
        setToast({ id: `${Date.now()}`, type: 'success', message: 'Benchmark suite refreshed successfully!' });
      }
    } catch (err) {
      setToast({ id: `${Date.now()}`, type: 'error', message: 'Failed to re-run benchmark evaluation.' });
    } finally {
      setIsEvalLoading(false);
    }
  };

  // Poll review status periodically while analyzing or running
  useEffect(() => {
    if (!activeJobId) return;

    const checkJob = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/review/${activeJobId}`);
        if (res.ok) {
          const data: ReviewJobResponse = await res.json();
          setReviewData(data);

          if (data.status === 'completed') {
            clearInterval(pollTimerRef.current);
            setIsLoading(false);
            setToast({
              id: `${Date.now()}`,
              type: 'success',
              message: `Review complete! ${data.findings_count} findings discovered.`
            });
          } else if (data.status === 'failed') {
            clearInterval(pollTimerRef.current);
            setIsLoading(false);
            setToast({
              id: `${Date.now()}`,
              type: 'error',
              message: data.error_message || 'Review job failed.'
            });
          }
        }
      } catch (e) {
        console.warn("Poll error", e);
      }
    };

    checkJob();
    pollTimerRef.current = setInterval(checkJob, 2000);

    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [activeJobId]);

  const handleSubmitReview = async (payload: ReviewSubmitPayload) => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Submission rejected');
      }

      const data = await res.json();
      setActiveJobId(data.job_id);
      setActiveTab('live');
      setToast({
        id: `${Date.now()}`,
        type: 'info',
        message: `Job ${data.job_id} launched. Streaming agent telemetry...`
      });
    } catch (err: any) {
      setIsLoading(false);
      setToast({
        id: `${Date.now()}`,
        type: 'error',
        message: err.message || 'Failed to submit review job.'
      });
    }
  };

  return (
    <div className="min-h-screen bg-bg-base text-fg-primary selection:bg-accent/20 selection:text-accent relative">
      {/* Divyansh Mishra Security & Ownership Watermark */}
      <WatermarkOverlay />

      {/* Primary Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isDark={isDark}
        setIsDark={setIsDark}
        activeJobId={activeJobId}
        jobStatus={reviewData?.status || null}
      />

      {/* Main Content Area */}
      <main className="relative z-10 pb-16">
        {activeTab === 'submit' && (
          <SubmitReview onSubmit={handleSubmitReview} isLoading={isLoading} />
        )}

        {activeTab === 'live' && (
          <LiveProgress 
            jobId={activeJobId} 
            onViewResults={() => setActiveTab('results')}
            reviewData={reviewData}
          />
        )}

        {activeTab === 'results' && (
          <ReviewResults reviewData={reviewData} />
        )}

        {activeTab === 'traces' && (
          <TraceTimeline 
            traces={reviewData?.traces || []} 
            jobId={activeJobId} 
          />
        )}

        {activeTab === 'evaluation' && (
          <EvalDashboard 
            evaluation={evaluation} 
            onRerun={handleRerunEvaluation}
            isLoading={isEvalLoading}
          />
        )}
      </main>

      {/* Floating Notifications */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};

export default App;
