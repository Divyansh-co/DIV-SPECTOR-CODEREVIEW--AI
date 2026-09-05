import asyncio
from app.retrieval.ast_chunker import chunk_python_code, chunk_js_ts_code
from app.retrieval.vector_store import LocalVectorStore
from app.retrieval.dependency_graph import DependencyGraph
from app.guardrails.validator import validate_syntax, apply_guardrails_to_finding
from app.evaluation.benchmarks import BENCHMARK_CASES
from app.evaluation.evaluator import BenchmarkEvaluator

def test_ast_chunking_python():
    code = """
def sample_func(a, b):
    \"\"\"Docstring test\"\"\"
    return a + b

class SampleClass:
    def method_one(self):
        return 42
"""
    chunks = chunk_python_code("sample.py", code)
    assert len(chunks) >= 2
    names = [c["name"] for c in chunks]
    assert "sample_func" in names
    assert "SampleClass" in names

def test_ast_chunking_javascript():
    code = """
function processData(input) {
    return input.toUpperCase();
}
const calculateTotal = (a, b) => {
    return a + b;
};
"""
    chunks = chunk_js_ts_code("sample.js", code, "javascript")
    assert len(chunks) >= 2
    names = [c["name"] for c in chunks]
    assert "processData" in names
    assert "calculateTotal" in names

def test_vector_store_indexing_and_search():
    store = LocalVectorStore()
    store.add_chunks([
        {"name": "authenticate_user", "content": "def authenticate_user(user, pw): verify token", "file_path": "auth.py", "unit_type": "function", "start_line": 1, "end_line": 5},
        {"name": "render_view", "content": "def render_view(template): return html", "file_path": "view.py", "unit_type": "function", "start_line": 1, "end_line": 5}
    ])
    results = store.search("authenticate token")
    assert len(results) > 0
    assert results[0]["name"] == "authenticate_user"

def test_guardrails_syntax_and_confidence():
    valid_py = "def fix(): return True"
    is_valid, _ = validate_syntax(valid_py, "python")
    assert is_valid is True

    invalid_py = "def fix( this is broken syntax :::"
    is_valid, err = validate_syntax(invalid_py, "python")
    assert is_valid is False

    # Below confidence threshold must NOT be safe to apply
    finding = {
        "suggested_fix": valid_py,
        "confidence": 0.65,
        "severity": "warning"
    }
    checked = apply_guardrails_to_finding(finding, "file.py", confidence_threshold=0.80)
    assert checked["is_safe_to_apply"] is False

    # Above confidence threshold + valid syntax -> safe to apply
    finding_high = {
        "suggested_fix": valid_py,
        "confidence": 0.95,
        "severity": "warning"
    }
    checked_high = apply_guardrails_to_finding(finding_high, "file.py", confidence_threshold=0.80)
    assert checked_high["is_safe_to_apply"] is True

def test_benchmark_evaluator_metrics():
    async def _run():
        evaluator = BenchmarkEvaluator()
        return await evaluator.run_evaluation()

    report = asyncio.run(_run())
    assert report.total_cases == len(BENCHMARK_CASES)
    assert report.precision >= 0.8
    assert report.recall >= 0.8
    assert report.f1_score >= 0.8
