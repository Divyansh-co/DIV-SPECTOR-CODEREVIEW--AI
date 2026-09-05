import ast
import time
from typing import Tuple, Optional, Dict, Any, List
from app.config import settings

def validate_syntax(code_snippet: str, language: str = "python") -> Tuple[bool, Optional[str]]:
    """
    Validates the syntax of a suggested fix before allowing it to be
    marked as 'safe to auto-apply'.
    """
    if not code_snippet or not code_snippet.strip():
        return False, "Empty snippet"

    clean_code = code_snippet.strip()
    # Strip markdown fences if present
    if clean_code.startswith("```"):
        lines = clean_code.splitlines()
        if len(lines) >= 2:
            clean_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    if language.lower() == "python":
        try:
            ast.parse(clean_code)
            return True, None
        except SyntaxError as e:
            # Often fixes are small expressions or statements, try parsing as expression or block
            try:
                ast.parse(f"def _temp():\n" + "\n".join(f"    {line}" for line in clean_code.splitlines()))
                return True, None
            except SyntaxError:
                return False, f"Python SyntaxError: {e.msg} at line {e.lineno}"

    elif language.lower() in ("javascript", "typescript", "js", "ts"):
        # Bracket & syntax balance check
        stack = []
        pairs = {')': '(', '}': '{', ']': '['}
        for char in clean_code:
            if char in "({[":
                stack.append(char)
            elif char in ")}]":
                if not stack or stack[-1] != pairs[char]:
                    return False, f"Mismatched bracket '{char}' in JavaScript fix"
                stack.pop()
        if stack:
            return False, f"Unclosed bracket '{stack[-1]}' in JavaScript fix"
        return True, None

    return True, None

def apply_guardrails_to_finding(
    finding: Dict[str, Any],
    file_path: str,
    confidence_threshold: float = 0.80
) -> Dict[str, Any]:
    """
    Applies strict guardrails to code review findings:
    1. Syntax checks suggested fixes.
    2. Enforces confidence thresholding.
    3. Guarantees is_safe_to_apply is only True if syntax is valid AND confidence >= threshold.
    """
    lang = "python" if file_path.endswith(".py") else "javascript"
    fix = finding.get("suggested_fix", "")
    confidence = float(finding.get("confidence", 0.5))

    syntax_valid, syntax_err = validate_syntax(fix, lang)
    finding["syntax_valid"] = syntax_valid

    # Guardrail rule: Fixes below confidence threshold are suggestion only, never auto-applied
    if confidence < confidence_threshold:
        finding["is_safe_to_apply"] = False
        if finding.get("severity") == "critical" and confidence < 0.5:
            # Downgrade if confidence is too weak
            finding["severity"] = "warning"
    else:
        # Only safe if syntax is valid
        finding["is_safe_to_apply"] = syntax_valid

    return finding

class RateLimiter:
    def __init__(self, max_calls_per_minute: int = 60):
        self.max_calls = max_calls_per_minute
        self.call_timestamps: List[float] = []

    def check_and_record(self) -> bool:
        now = time.time()
        # Evict timestamps older than 60s
        self.call_timestamps = [t for t in self.call_timestamps if now - t < 60]
        if len(self.call_timestamps) >= self.max_calls:
            return False
        self.call_timestamps.append(now)
        return True
