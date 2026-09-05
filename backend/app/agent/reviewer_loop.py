import json
import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from app.config import settings
from app.models.schemas import (
    ReviewSubmitRequest, ReviewJobResponse, CodeFinding, AgentToolTrace,
    JobStatus, SeverityEnum, CategoryEnum
)
from app.db.database import (
    create_review_job, update_job_status, save_finding, save_trace, get_review_job
)
from app.ingestion.scanner import scan_directory
from app.ingestion.diff_parser import parse_git_diff
from app.ingestion.git_clone import clone_repository, extract_git_diff
from app.retrieval.ast_chunker import chunk_file
from app.retrieval.dependency_graph import DependencyGraph
from app.retrieval.vector_store import LocalVectorStore
from app.tools.runner import TOOL_DEFINITIONS, ToolExecutor
from app.agent.prompt import SYSTEM_PROMPT, DIFF_REVIEW_PROMPT_TEMPLATE, FULL_SCAN_PROMPT_TEMPLATE
from app.agent.llm_client import LLMClient
from app.guardrails.validator import apply_guardrails_to_finding, RateLimiter

class ReviewerAgent:
    def __init__(self):
        self.llm_client = LLMClient()
        self.rate_limiter = RateLimiter(settings.RATE_LIMIT_PER_MINUTE)

    async def run_review(
        self,
        job_id: str,
        request: ReviewSubmitRequest,
        ws_broadcast: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> ReviewJobResponse:
        """
        Executes autonomous multi-step review with tool calling, 
        guardrails, and real-time streaming updates.
        """
        async def broadcast(event_type: str, data: Dict[str, Any]):
            if ws_broadcast:
                payload = {
                    "type": event_type,
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **data
                }
                try:
                    res = ws_broadcast(payload)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    pass

        try:
            target_name = Path(request.path_or_url).name or request.path_or_url
            await create_review_job(job_id, request.target_type, target_name, request.mode.value)
            await update_job_status(job_id, JobStatus.ANALYZING)
            await broadcast("status_update", {"status": "analyzing", "message": "Preparing codebase and building AST..."})

            # 1. Resolve workspace root
            if request.target_type == "git_url":
                await broadcast("log", {"message": f"Cloning repository {request.path_or_url}..."})
                workspace_path = clone_repository(request.path_or_url, job_id)
            else:
                workspace_path = Path(request.path_or_url)
                if not workspace_path.exists():
                    raise ValueError(f"Directory does not exist: {workspace_path}")

            # 2. Ingestion: Scan and chunk files
            await broadcast("log", {"message": f"Scanning files in {workspace_path}..."})
            scanned_files = scan_directory(str(workspace_path))
            if not scanned_files:
                raise ValueError(f"No supported source files (.py, .js, .ts) found in {workspace_path}")

            await broadcast("log", {"message": f"Indexed {len(scanned_files)} files. Building AST dependency graph & vector store..."})

            # Vector Store & AST Chunking
            vector_store = LocalVectorStore()
            for f in scanned_files:
                chunks = chunk_file(f)
                vector_store.add_chunks(chunks)

            # Dependency Graph
            dep_graph = DependencyGraph()
            dep_graph.build_from_files(scanned_files)

            tool_executor = ToolExecutor(str(workspace_path), vector_store, dep_graph)

            # 3. Formulate Prompt based on Mode
            user_prompt = ""
            if request.mode == "diff":
                diff_text = request.diff_content or ""
                if not diff_text and request.base_ref and request.head_ref:
                    diff_text = extract_git_diff(workspace_path, request.base_ref, request.head_ref)

                diff_analysis = parse_git_diff(diff_text)
                changed_files = [d["file_path"] for d in diff_analysis]
                changed_functions = []
                for d in diff_analysis:
                    for hunk in d.get("hunks", []):
                        for num in hunk.get("changed_line_numbers", []):
                            # match with file chunks
                            for ch in vector_store.chunks:
                                if ch["file_path"] == d["file_path"] and ch["start_line"] <= num <= ch["end_line"]:
                                    changed_functions.append(ch["name"])

                diff_context = dep_graph.get_diff_context(changed_files, list(set(changed_functions)))
                user_prompt = DIFF_REVIEW_PROMPT_TEMPLATE.format(
                    changed_files=", ".join(changed_files) or "None detected",
                    callers=json.dumps(diff_context.get("changed_function_callers", {})),
                    tests=", ".join(diff_context.get("relevant_test_files", [])) or "None found",
                    diff_text=diff_text or "No diff text provided."
                )
            else:
                top_files = [f["path"] for f in scanned_files[:15]]
                user_prompt = FULL_SCAN_PROMPT_TEMPLATE.format(
                    repo_name=target_name,
                    file_count=len(scanned_files),
                    file_list=", ".join(top_files)
                )

            if request.custom_rules:
                user_prompt += f"\n\nADDITIONAL USER REVIEW RULES:\n{request.custom_rules}"

            # 4. Multi-turn Agent Loop
            await update_job_status(job_id, JobStatus.RUNNING_TOOLS)
            await broadcast("status_update", {"status": "running_tools", "message": "Principal Agent investigating with tools..."})

            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]

            step_count = 0
            traces: List[AgentToolTrace] = []
            final_content = ""

            while step_count < settings.MAX_ITERATIONS:
                step_count += 1
                self.rate_limiter.check_and_record()

                # Call LLM
                response = await self.llm_client.call_completion(
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto"
                )

                content = response.get("content") or ""
                tool_calls = response.get("tool_calls") or []

                if not tool_calls:
                    # Final synthesis reached
                    final_content = content
                    break

                # Process Tool Calls
                tool_call_records = []
                for tc in tool_calls:
                    tc_id = tc.get("id") or f"call_{uuid.uuid4().hex[:6]}"
                    func_obj = tc.get("function", {})
                    fn_name = func_obj.get("name")
                    try:
                        fn_args = json.loads(func_obj.get("arguments", "{}"))
                    except Exception:
                        fn_args = {"raw": func_obj.get("arguments", "")}

                    await broadcast("trace_start", {
                        "step": step_count,
                        "tool": fn_name,
                        "args": fn_args,
                        "thought": content[:200] if content else f"Executing {fn_name}..."
                    })

                    # Execute tool
                    tool_result = tool_executor.execute_tool(fn_name, fn_args)

                    trace_record = AgentToolTrace(
                        id=f"trace_{uuid.uuid4().hex[:8]}",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        step_number=step_count,
                        thought=content,
                        tool_name=fn_name,
                        tool_input=fn_args,
                        tool_output=tool_result["tool_output"],
                        duration_ms=tool_result["duration_ms"],
                        status=tool_result["status"]
                    )
                    traces.append(trace_record)
                    await save_trace(job_id, trace_record)

                    await broadcast("trace_end", {
                        "step": step_count,
                        "tool": fn_name,
                        "status": tool_result["status"],
                        "duration_ms": tool_result["duration_ms"],
                        "output_preview": tool_result["tool_output"][:160]
                    })

                    tool_call_records.append({
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": fn_name,
                            "arguments": json.dumps(fn_args)
                        }
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "name": fn_name,
                        "content": tool_result["tool_output"]
                    })

                # Append assistant tool calls to message history
                messages.insert(-len(tool_calls), {
                    "role": "assistant",
                    "content": content,
                    "tool_calls": tool_call_records
                })

            # If loop exited after max iterations without final text, ask for synthesis
            if not final_content:
                messages.append({
                    "role": "user",
                    "content": "You have completed your tool investigation. Return your final findings in the required JSON format now."
                })
                synthesis_resp = await self.llm_client.call_completion(messages, tools=None)
                final_content = synthesis_resp.get("content") or ""

            # 5. Parse Findings and Apply Guardrails
            await update_job_status(job_id, JobStatus.SYNTHESIZING)
            await broadcast("status_update", {"status": "synthesizing", "message": "Validating syntax & applying confidence guardrails..."})

            parsed_findings, summary = self._extract_json_findings(final_content)
            findings_objects: List[CodeFinding] = []

            for raw_f in parsed_findings:
                # Apply guardrails (syntax validation, confidence gating)
                validated = apply_guardrails_to_finding(
                    raw_f,
                    file_path=raw_f.get("file_path", "unknown"),
                    confidence_threshold=settings.CONFIDENCE_THRESHOLD
                )

                # Attempt to extract original snippet if file exists
                orig_snippet = None
                try:
                    fpath = workspace_path / validated.get("file_path", "")
                    if fpath.exists() and fpath.is_file():
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f_obj:
                            all_lines = f_obj.readlines()
                        l_start = max(1, validated.get("line_number", 1))
                        l_end = min(len(all_lines), validated.get("end_line_number") or l_start + 4)
                        orig_snippet = "".join(all_lines[l_start - 1:l_end])
                except Exception:
                    pass

                finding_obj = CodeFinding(
                    id=f"find_{uuid.uuid4().hex[:8]}",
                    severity=SeverityEnum(validated.get("severity", "warning").lower()),
                    category=CategoryEnum(validated.get("category", "bug").lower()),
                    file_path=validated.get("file_path", "unknown"),
                    line_number=validated.get("line_number", 1),
                    end_line_number=validated.get("end_line_number"),
                    explanation=validated.get("explanation", "Potential issue identified during review."),
                    suggested_fix=validated.get("suggested_fix", "# Check logic"),
                    confidence=float(validated.get("confidence", 0.8)),
                    is_safe_to_apply=bool(validated.get("is_safe_to_apply", False)),
                    syntax_valid=bool(validated.get("syntax_valid", False)),
                    original_snippet=orig_snippet
                )
                findings_objects.append(finding_obj)
                await save_finding(job_id, finding_obj)

            # 6. Complete Job
            await update_job_status(job_id, JobStatus.COMPLETED, summary=summary)
            await broadcast("completed", {
                "summary": summary,
                "findings_count": len(findings_objects),
                "critical_count": sum(1 for f in findings_objects if f.severity == SeverityEnum.CRITICAL),
                "warning_count": sum(1 for f in findings_objects if f.severity == SeverityEnum.WARNING),
                "suggestion_count": sum(1 for f in findings_objects if f.severity == SeverityEnum.SUGGESTION)
            })

            return await get_review_job(job_id)

        except Exception as e:
            error_msg = str(e)
            await update_job_status(job_id, JobStatus.FAILED, error_message=error_msg)
            await broadcast("error", {"error": error_msg})
            return await get_review_job(job_id)

    def _extract_json_findings(self, text: str) -> (List[Dict[str, Any]], str):
        """
        Extracts structured findings and summary from LLM response text.
        """
        # Look for ```json ... ``` blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        candidate_str = json_match.group(1) if json_match else text

        try:
            data = json.loads(candidate_str)
            summary = data.get("summary", "Code review completed.")
            findings = data.get("findings", [])
            if isinstance(findings, list):
                return findings, summary
        except Exception:
            pass

        # Try regex fallback for json array
        arr_match = re.search(r"(\[\s*\{.*?\}\s*\])", text, re.DOTALL)
        if arr_match:
            try:
                findings = json.loads(arr_match.group(1))
                if isinstance(findings, list):
                    return findings, "Automated code review completed."
            except Exception:
                pass

        # Fallback summary
        return [], text[:300] if text else "Review completed with no critical findings."
