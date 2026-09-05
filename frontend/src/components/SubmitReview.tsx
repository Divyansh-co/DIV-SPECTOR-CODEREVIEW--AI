import React, { useState } from 'react';
import { 
  FolderGit2, Globe, GitPullRequest, SearchCode, 
  Sparkles, ArrowRight, CheckCircle2 
} from 'lucide-react';
import type { ReviewSubmitPayload } from '../types';

interface SubmitReviewProps {
  onSubmit: (payload: ReviewSubmitPayload) => void;
  isLoading: boolean;
}

export const SubmitReview: React.FC<SubmitReviewProps> = ({ onSubmit, isLoading }) => {
  const [targetType, setTargetType] = useState<'local_path' | 'git_url'>('local_path');
  const [pathOrUrl, setPathOrUrl] = useState<string>('C:\\ai-code-reviewer\\backend');
  const [mode, setMode] = useState<'full_scan' | 'diff'>('full_scan');
  const [diffContent, setDiffContent] = useState<string>('');
  const [customRules, setCustomRules] = useState<string>('');

  const handlePresetDiffPython = () => {
    setTargetType('local_path');
    setPathOrUrl('C:\\ai-code-reviewer\\backend');
    setMode('diff');
    setDiffContent(`diff --git a/app/services/auth.py b/app/services/auth.py
index 4b825dc..a71f002 100644
--- a/app/services/auth.py
+++ b/app/services/auth.py
@@ -10,6 +10,12 @@ def verify_login(db_conn, username, password):
-    cursor = db_conn.cursor()
-    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
+    cursor = db_conn.cursor()
+    # Changed query for dynamic tenant lookup
+    query = f"SELECT id, role FROM users WHERE username = '{username}' AND password = '{password}'"
+    cursor.execute(query)
+    user = cursor.fetchone()
+    return user
diff --git a/app/services/user_service.py b/app/services/user_service.py
index 1029ab..3910fc 100644
--- a/app/services/user_service.py
+++ b/app/services/user_service.py
@@ -25,4 +25,7 @@ def get_email(user_records, user_id):
+    record = user_records.get(user_id)
+    profile = record.get("profile")
+    return profile["contact"]["email"].lower()
`);
  };

  const handlePresetDiffJs = () => {
    setTargetType('local_path');
    setPathOrUrl('C:\\ai-code-reviewer\\backend');
    setMode('diff');
    setDiffContent(`diff --git a/src/api/users.js b/src/api/users.js
index 81726a..92837b 100644
--- a/src/api/users.js
+++ b/src/api/users.js
@@ -1,5 +1,10 @@
 export function syncUserProfile(userId, payload) {
-  return api.post(\`/users/\${userId}\`, payload);
+  return fetch(\`/api/users/\${userId}\`, {
+    method: 'POST',
+    headers: { 'Content-Type': 'application/json' },
+    body: JSON.stringify(payload)
+  })
+  .then(res => res.json())
+  .then(data => data.status);
 }
`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pathOrUrl.trim()) return;

    onSubmit({
      target_type: targetType,
      path_or_url: pathOrUrl.trim(),
      mode,
      diff_content: mode === 'diff' ? diffContent : undefined,
      custom_rules: customRules.trim() || undefined
    });
  };

  return (
    <div className="mx-auto max-w-4xl py-6 px-4">
      {/* Title & Header Banner */}
      <div className="mb-6 rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <div className="inline-flex items-center space-x-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1 text-xs font-mono text-accent">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Multi-Turn Senior Engineer Agent Loop</span>
            </div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-fg-primary">
              Initiate Code Review Investigation
            </h1>
            <p className="mt-1 text-sm text-fg-secondary">
              Specter indexes your codebase into AST semantic chunks, builds dependency call graphs, executes tools in an isolated sandbox, and reports precision-audited findings.
            </p>
          </div>
          <div className="hidden sm:flex flex-col items-end text-xs text-fg-muted font-mono">
            <span>ENGINEER</span>
            <span className="font-semibold text-accent">Divyansh Mishra</span>
          </div>
        </div>

        {/* Quick Demo Presets */}
        <div className="mt-4 pt-4 border-t border-border-subtle flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-fg-muted">Quick Demos:</span>
          <button
            type="button"
            onClick={() => {
              setTargetType('local_path');
              setPathOrUrl('C:\\ai-code-reviewer\\backend');
              setMode('full_scan');
            }}
            className="rounded-md border border-border-highlight bg-bg-overlay px-2.5 py-1 text-xs font-mono text-fg-secondary hover:text-accent hover:border-accent/40 transition-colors"
          >
            ⚡ Full Scan: Specter Backend
          </button>
          <button
            type="button"
            onClick={handlePresetDiffPython}
            className="rounded-md border border-border-highlight bg-bg-overlay px-2.5 py-1 text-xs font-mono text-fg-secondary hover:text-sev-critical hover:border-sev-critical/40 transition-colors"
          >
            🛡️ PR Diff: SQLi & Null Deref Flaws
          </button>
          <button
            type="button"
            onClick={handlePresetDiffJs}
            className="rounded-md border border-border-highlight bg-bg-overlay px-2.5 py-1 text-xs font-mono text-fg-secondary hover:text-sev-warning hover:border-sev-warning/40 transition-colors"
          >
            ⚙️ PR Diff: Unhandled Async Fetch
          </button>
        </div>
      </div>

      {/* Review Submission Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-xl border border-border-subtle bg-bg-surface p-6 shadow-sm space-y-5">
          
          {/* Input Type Selection */}
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-fg-muted mb-2">
              Source Location Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setTargetType('local_path')}
                className={`flex items-center justify-center space-x-2 rounded-lg border p-3 text-sm font-medium transition-all ${
                  targetType === 'local_path'
                    ? 'border-accent bg-accent/10 text-accent font-semibold'
                    : 'border-border-subtle bg-bg-base text-fg-secondary hover:border-border-highlight'
                }`}
              >
                <FolderGit2 className="h-4 w-4" />
                <span>Local Directory Path</span>
              </button>
              <button
                type="button"
                onClick={() => setTargetType('git_url')}
                className={`flex items-center justify-center space-x-2 rounded-lg border p-3 text-sm font-medium transition-all ${
                  targetType === 'git_url'
                    ? 'border-accent bg-accent/10 text-accent font-semibold'
                    : 'border-border-subtle bg-bg-base text-fg-secondary hover:border-border-highlight'
                }`}
              >
                <Globe className="h-4 w-4" />
                <span>Git Remote URL</span>
              </button>
            </div>
          </div>

          {/* Path or URL Input */}
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-fg-muted mb-1.5">
              {targetType === 'local_path' ? 'Absolute Workspace Directory' : 'Git Repository Clone URL'}
            </label>
            <input
              type="text"
              value={pathOrUrl}
              onChange={(e) => setPathOrUrl(e.target.value)}
              placeholder={targetType === 'local_path' ? 'C:\\projects\\my-app or /home/user/code' : 'https://github.com/org/repo.git'}
              className="w-full rounded-lg border border-border-subtle bg-bg-base px-3.5 py-2.5 text-sm font-mono text-fg-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              required
            />
          </div>

          {/* Mode Selection */}
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-fg-muted mb-2">
              Analysis Scope Mode
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setMode('full_scan')}
                className={`flex items-center justify-center space-x-2 rounded-lg border p-3 text-sm font-medium transition-all ${
                  mode === 'full_scan'
                    ? 'border-accent bg-accent/10 text-accent font-semibold'
                    : 'border-border-subtle bg-bg-base text-fg-secondary hover:border-border-highlight'
                }`}
              >
                <SearchCode className="h-4 w-4" />
                <span>Full Codebase Scan</span>
              </button>
              <button
                type="button"
                onClick={() => setMode('diff')}
                className={`flex items-center justify-center space-x-2 rounded-lg border p-3 text-sm font-medium transition-all ${
                  mode === 'diff'
                    ? 'border-accent bg-accent/10 text-accent font-semibold'
                    : 'border-border-subtle bg-bg-base text-fg-secondary hover:border-border-highlight'
                }`}
              >
                <GitPullRequest className="h-4 w-4" />
                <span>Git Diff / PR Mode</span>
              </button>
            </div>
          </div>

          {/* Git Diff Content Textarea (if diff mode) */}
          {mode === 'diff' && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-fg-muted">
                  Unified Git Diff Payload
                </label>
                <span className="text-[11px] font-mono text-fg-muted">diff --git a/... b/... format</span>
              </div>
              <textarea
                rows={7}
                value={diffContent}
                onChange={(e) => setDiffContent(e.target.value)}
                placeholder={`diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,4 +1,4 @@\n- old_code()\n+ new_code()`}
                className="w-full rounded-lg border border-border-subtle bg-bg-code p-3 text-xs font-mono text-fg-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
          )}

          {/* Custom Rules */}
          <div>
            <label className="block text-xs font-medium uppercase tracking-wider text-fg-muted mb-1.5">
              Custom Review Directives / Constraints (Optional)
            </label>
            <input
              type="text"
              value={customRules}
              onChange={(e) => setCustomRules(e.target.value)}
              placeholder="e.g. Enforce strict parameter typing, audit for OWASP Top 10 vulnerabilities..."
              className="w-full rounded-lg border border-border-subtle bg-bg-base px-3.5 py-2 text-sm text-fg-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>

        </div>

        {/* Submit Action */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-fg-muted">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>AST Chunking • Vector Store • Sandboxed Subprocesses Enabled</span>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center space-x-2 rounded-lg bg-accent px-6 py-2.5 text-sm font-semibold text-slate-950 hover:bg-accent-hover shadow-lg hover:shadow-accent/20 transition-all disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <span className="h-4 w-4 rounded-full border-2 border-slate-950 border-t-transparent animate-spin" />
                <span>Launching Agent...</span>
              </>
            ) : (
              <>
                <span>Launch Review Agent</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

      </form>
    </div>
  );
};
