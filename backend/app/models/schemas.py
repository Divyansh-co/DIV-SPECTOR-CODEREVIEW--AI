from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"

class CategoryEnum(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"

class ReviewMode(str, Enum):
    FULL_SCAN = "full_scan"
    DIFF = "diff"

class JobStatus(str, Enum):
    QUEUED = "queued"
    ANALYZING = "analyzing"
    RUNNING_TOOLS = "running_tools"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"

class ReviewSubmitRequest(BaseModel):
    target_type: str = Field(default="local_path", description="'local_path' or 'git_url'")
    path_or_url: str = Field(..., description="Absolute local path or git clone URL")
    mode: ReviewMode = Field(default=ReviewMode.FULL_SCAN, description="'full_scan' or 'diff'")
    diff_content: Optional[str] = Field(default=None, description="Raw git diff if review mode is diff")
    base_ref: Optional[str] = Field(default=None, description="Base branch or commit hash")
    head_ref: Optional[str] = Field(default=None, description="Head branch or commit hash")
    custom_rules: Optional[str] = Field(default=None, description="Optional extra instructions for the reviewer")

class CodeFinding(BaseModel):
    id: str
    severity: SeverityEnum
    category: CategoryEnum
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    explanation: str
    suggested_fix: str
    confidence: float = Field(ge=0.0, le=1.0)
    is_safe_to_apply: bool = False
    syntax_valid: bool = False
    original_snippet: Optional[str] = None

class AgentToolTrace(BaseModel):
    id: str
    timestamp: str
    step_number: int
    thought: Optional[str] = None
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: str
    duration_ms: int
    status: str = "success"

class ReviewJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: str
    completed_at: Optional[str] = None
    target_type: str
    target_name: str
    mode: str
    summary: Optional[str] = None
    findings_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    suggestion_count: int = 0
    findings: List[CodeFinding] = []
    traces: List[AgentToolTrace] = []
    error_message: Optional[str] = None

class BenchmarkCase(BaseModel):
    case_id: str
    title: str
    description: str
    language: str  # python, javascript, typescript
    category: CategoryEnum
    expected_defect_line: int
    expected_severity: SeverityEnum
    code_snippet: str
    ground_truth_explanation: str

class BenchmarkEvaluationReport(BaseModel):
    total_cases: int
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    evaluated_at: str
    category_metrics: Dict[str, Dict[str, float]]
    cases: List[Dict[str, Any]]
