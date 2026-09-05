import json
import aiosqlite
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.config import settings
from app.models.schemas import (
    ReviewJobResponse, CodeFinding, AgentToolTrace, JobStatus,
    BenchmarkEvaluationReport
)

async def init_db():
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                job_id TEXT PRIMARY KEY,
                target_type TEXT,
                target_name TEXT,
                mode TEXT,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                summary TEXT,
                error_message TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                severity TEXT,
                category TEXT,
                file_path TEXT,
                line_number INTEGER,
                end_line_number INTEGER,
                explanation TEXT,
                suggested_fix TEXT,
                confidence REAL,
                is_safe_to_apply INTEGER,
                syntax_valid INTEGER,
                original_snippet TEXT,
                FOREIGN KEY (job_id) REFERENCES reviews (job_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_traces (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                step_number INTEGER,
                timestamp TEXT,
                thought TEXT,
                tool_name TEXT,
                tool_input TEXT,
                tool_output TEXT,
                duration_ms INTEGER,
                status TEXT,
                FOREIGN KEY (job_id) REFERENCES reviews (job_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_evaluations (
                id TEXT PRIMARY KEY,
                evaluated_at TEXT,
                report_json TEXT
            )
        """)
        await db.commit()

async def create_review_job(job_id: str, target_type: str, target_name: str, mode: str):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """INSERT INTO reviews (job_id, target_type, target_name, mode, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (job_id, target_type, target_name, mode, JobStatus.QUEUED.value, now)
        )
        await db.commit()

async def update_job_status(job_id: str, status: JobStatus, summary: Optional[str] = None, error_message: Optional[str] = None):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        now = datetime.now(timezone.utc).isoformat() if status in [JobStatus.COMPLETED, JobStatus.FAILED] else None
        await db.execute(
            """UPDATE reviews 
               SET status = ?, 
                   summary = COALESCE(?, summary), 
                   error_message = ?, 
                   completed_at = COALESCE(?, completed_at)
               WHERE job_id = ?""",
            (status.value, summary, error_message, now, job_id)
        )
        await db.commit()

async def save_finding(job_id: str, finding: CodeFinding):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            """INSERT INTO findings (
                id, job_id, severity, category, file_path, line_number,
                end_line_number, explanation, suggested_fix, confidence,
                is_safe_to_apply, syntax_valid, original_snippet
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                finding.id, job_id, finding.severity.value, finding.category.value,
                finding.file_path, finding.line_number, finding.end_line_number,
                finding.explanation, finding.suggested_fix, finding.confidence,
                1 if finding.is_safe_to_apply else 0,
                1 if finding.syntax_valid else 0,
                finding.original_snippet
            )
        )
        await db.commit()

async def save_trace(job_id: str, trace: AgentToolTrace):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            """INSERT INTO agent_traces (
                id, job_id, step_number, timestamp, thought, tool_name,
                tool_input, tool_output, duration_ms, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace.id, job_id, trace.step_number, trace.timestamp,
                trace.thought, trace.tool_name, json.dumps(trace.tool_input),
                trace.tool_output, trace.duration_ms, trace.status
            )
        )
        await db.commit()

async def get_review_job(job_id: str) -> Optional[ReviewJobResponse]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM reviews WHERE job_id = ?", (job_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            # Fetch findings
            findings: List[CodeFinding] = []
            async with db.execute("SELECT * FROM findings WHERE job_id = ? ORDER BY line_number ASC", (job_id,)) as f_cursor:
                f_rows = await f_cursor.fetchall()
                for fr in f_rows:
                    findings.append(CodeFinding(
                        id=fr["id"],
                        severity=fr["severity"],
                        category=fr["category"],
                        file_path=fr["file_path"],
                        line_number=fr["line_number"],
                        end_line_number=fr["end_line_number"],
                        explanation=fr["explanation"],
                        suggested_fix=fr["suggested_fix"],
                        confidence=fr["confidence"],
                        is_safe_to_apply=bool(fr["is_safe_to_apply"]),
                        syntax_valid=bool(fr["syntax_valid"]),
                        original_snippet=fr["original_snippet"]
                    ))

            # Fetch traces
            traces: List[AgentToolTrace] = []
            async with db.execute("SELECT * FROM agent_traces WHERE job_id = ? ORDER BY step_number ASC", (job_id,)) as t_cursor:
                t_rows = await t_cursor.fetchall()
                for tr in t_rows:
                    try:
                        tool_input = json.loads(tr["tool_input"])
                    except Exception:
                        tool_input = {"raw": tr["tool_input"]}
                    traces.append(AgentToolTrace(
                        id=tr["id"],
                        timestamp=tr["timestamp"],
                        step_number=tr["step_number"],
                        thought=tr["thought"],
                        tool_name=tr["tool_name"],
                        tool_input=tool_input,
                        tool_output=tr["tool_output"],
                        duration_ms=tr["duration_ms"],
                        status=tr["status"]
                    ))

            crit = sum(1 for f in findings if f.severity == "critical")
            warn = sum(1 for f in findings if f.severity == "warning")
            sugg = sum(1 for f in findings if f.severity == "suggestion")

            return ReviewJobResponse(
                job_id=row["job_id"],
                status=row["status"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
                target_type=row["target_type"],
                target_name=row["target_name"],
                mode=row["mode"],
                summary=row["summary"],
                findings_count=len(findings),
                critical_count=crit,
                warning_count=warn,
                suggestion_count=sugg,
                findings=findings,
                traces=traces,
                error_message=row["error_message"]
            )

async def get_all_reviews() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT r.*, 
                   COUNT(f.id) as findings_count,
                   SUM(CASE WHEN f.severity = 'critical' THEN 1 ELSE 0 END) as critical_count
            FROM reviews r
            LEFT JOIN findings f ON r.job_id = f.job_id
            GROUP BY r.job_id
            ORDER BY r.created_at DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def save_evaluation_report(eval_id: str, report: BenchmarkEvaluationReport):
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO benchmark_evaluations (id, evaluated_at, report_json) VALUES (?, ?, ?)",
            (eval_id, report.evaluated_at, report.model_dump_json())
        )
        await db.commit()

async def get_latest_evaluation() -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM benchmark_evaluations ORDER BY evaluated_at DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row["report_json"])
            return None
