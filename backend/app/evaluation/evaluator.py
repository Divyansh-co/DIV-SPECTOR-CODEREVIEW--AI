import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.evaluation.benchmarks import BENCHMARK_CASES
from app.models.schemas import BenchmarkEvaluationReport, BenchmarkCase
from app.agent.llm_client import LLMClient
from app.db.database import save_evaluation_report

class BenchmarkEvaluator:
    def __init__(self):
        self.llm_client = LLMClient()

    async def run_evaluation(self) -> BenchmarkEvaluationReport:
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        category_stats: Dict[str, Dict[str, int]] = {
            "security": {"tp": 0, "fp": 0, "fn": 0, "total": 0},
            "bug": {"tp": 0, "fp": 0, "fn": 0, "total": 0},
            "performance": {"tp": 0, "fp": 0, "fn": 0, "total": 0},
            "maintainability": {"tp": 0, "fp": 0, "fn": 0, "total": 0},
        }

        case_results: List[Dict[str, Any]] = []

        for case in BENCHMARK_CASES:
            cat_name = case.category.value
            if cat_name in category_stats:
                category_stats[cat_name]["total"] += 1

            # Run detection logic
            # Simulate or call LLM detection on benchmark code snippet
            findings = self.llm_client._detect_code_defects(case.code_snippet)

            # Evaluate control case
            if case.case_id == "bench_12_clean_control":
                # Expect zero critical or warning bugs
                high_severity_findings = [f for f in findings if f.get("severity") in ("critical", "warning")]
                if len(high_severity_findings) > 0:
                    false_positives += 1
                    status = "FAIL (False Positive)"
                else:
                    status = "PASS"

                case_results.append({
                    "case_id": case.case_id,
                    "title": case.title,
                    "category": cat_name,
                    "expected_line": case.expected_defect_line,
                    "status": status,
                    "detected_findings": len(findings),
                    "description": case.description
                })
                continue

            # Standard defect case
            detected = False
            for f in findings:
                # Check category match and reasonable line proximity or flaw keywords
                f_cat = f.get("category", "")
                f_line = f.get("line_number", 0)
                f_expl = f.get("explanation", "").lower()

                # If category matches or explanation highlights the flaw
                if (f_cat == cat_name or cat_name in f_expl or abs(f_line - case.expected_defect_line) <= 4):
                    detected = True
                    break

            if detected:
                true_positives += 1
                if cat_name in category_stats:
                    category_stats[cat_name]["tp"] += 1
                status = "PASS"
            else:
                false_negatives += 1
                if cat_name in category_stats:
                    category_stats[cat_name]["fn"] += 1
                status = "FAIL (Missed Defect)"

            case_results.append({
                "case_id": case.case_id,
                "title": case.title,
                "category": cat_name,
                "expected_line": case.expected_defect_line,
                "status": status,
                "detected_findings": len(findings),
                "description": case.description
            })

        # Calculate overall metrics
        total_eval = true_positives + false_positives
        precision = (true_positives / total_eval) if total_eval > 0 else 1.0
        recall = (true_positives / (true_positives + false_negatives)) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        # Calculate category breakdown metrics
        cat_metrics: Dict[str, Dict[str, float]] = {}
        for c_name, stats in category_stats.items():
            c_tp = stats["tp"]
            c_fp = stats["fp"]
            c_fn = stats["fn"]
            c_prec = (c_tp / (c_tp + c_fp)) if (c_tp + c_fp) > 0 else 1.0
            c_rec = (c_tp / (c_tp + c_fn)) if (c_tp + c_fn) > 0 else 0.0
            c_f1 = (2 * c_prec * c_rec / (c_prec + c_rec)) if (c_prec + c_rec) > 0 else 0.0
            cat_metrics[c_name] = {
                "precision": round(c_prec, 3),
                "recall": round(c_rec, 3),
                "f1_score": round(c_f1, 3),
                "total_cases": stats["total"]
            }

        report = BenchmarkEvaluationReport(
            total_cases=len(BENCHMARK_CASES),
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1_score, 3),
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            category_metrics=cat_metrics,
            cases=case_results
        )

        eval_id = f"eval_{uuid.uuid4().hex[:8]}"
        await save_evaluation_report(eval_id, report)
        return report
