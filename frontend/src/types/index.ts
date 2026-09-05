export type Severity = 'critical' | 'warning' | 'suggestion';
export type Category = 'bug' | 'security' | 'performance' | 'style' | 'maintainability';
export type ReviewMode = 'full_scan' | 'diff';
export type JobStatus = 'queued' | 'analyzing' | 'running_tools' | 'synthesizing' | 'completed' | 'failed';

export interface CodeFinding {
  id: string;
  severity: Severity;
  category: Category;
  file_path: string;
  line_number: number;
  end_line_number?: number;
  explanation: string;
  suggested_fix: string;
  confidence: number;
  is_safe_to_apply: boolean;
  syntax_valid: boolean;
  original_snippet?: string;
}

export interface AgentToolTrace {
  id: string;
  timestamp: string;
  step_number: number;
  thought?: string;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output: string;
  duration_ms: number;
  status: string;
}

export interface ReviewJobResponse {
  job_id: string;
  status: JobStatus;
  created_at: string;
  completed_at?: string;
  target_type: string;
  target_name: string;
  mode: string;
  summary?: string;
  findings_count: number;
  critical_count: number;
  warning_count: number;
  suggestion_count: number;
  findings: CodeFinding[];
  traces: AgentToolTrace[];
  error_message?: string;
}

export interface CategoryMetric {
  precision: number;
  recall: number;
  f1_score: number;
  total_cases: number;
}

export interface BenchmarkCaseResult {
  case_id: string;
  title: string;
  category: string;
  expected_line: number;
  status: string;
  detected_findings: number;
  description: string;
}

export interface BenchmarkEvaluationReport {
  total_cases: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
  evaluated_at: string;
  category_metrics: Record<string, CategoryMetric>;
  cases: BenchmarkCaseResult[];
}

export interface ReviewSubmitPayload {
  target_type: 'local_path' | 'git_url';
  path_or_url: string;
  mode: ReviewMode;
  diff_content?: string;
  base_ref?: string;
  head_ref?: string;
  custom_rules?: string;
}
