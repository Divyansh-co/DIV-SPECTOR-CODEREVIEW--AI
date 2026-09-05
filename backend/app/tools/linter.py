import subprocess
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings

def run_linter(file_path: str, workspace_root: str) -> Dict[str, Any]:
    """
    Executes linter (flake8 for Python, node/eslint for JS) on target file
    within sandboxed subprocess with timeout.
    """
    full_path = Path(workspace_root) / file_path
    if not full_path.exists():
        return {
            "status": "error",
            "file": file_path,
            "error": f"File not found: {file_path}",
            "violations": []
        }

    ext = full_path.suffix.lower()

    if ext == ".py":
        # Run flake8 via sys.executable
        cmd = [
            sys.executable, "-m", "flake8",
            "--max-line-length=120",
            "--select=E,W,F,C",
            str(full_path)
        ]
        try:
            res = subprocess.run(
                cmd,
                cwd=workspace_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=settings.TOOL_TIMEOUT_SECONDS
            )
            raw_output = res.stdout.strip()
            violations: List[Dict[str, Any]] = []
            for line in raw_output.splitlines():
                parts = line.split(":", 3)
                if len(parts) >= 4:
                    violations.append({
                        "file": file_path,
                        "line": int(parts[1].strip()) if parts[1].strip().isdigit() else 1,
                        "col": int(parts[2].strip()) if parts[2].strip().isdigit() else 1,
                        "message": parts[3].strip()
                    })

            return {
                "status": "success",
                "file": file_path,
                "tool": "flake8",
                "violation_count": len(violations),
                "violations": violations,
                "raw_output": raw_output or "No linter violations found."
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "file": file_path,
                "error": f"Linter timed out after {settings.TOOL_TIMEOUT_SECONDS}s",
                "violations": []
            }
        except Exception as e:
            return {
                "status": "error",
                "file": file_path,
                "error": str(e),
                "violations": []
            }

    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        # If node is available, do a syntax/lint check
        node_bin = shutil.which("node")
        if node_bin:
            cmd = [node_bin, "--check", str(full_path)]
            try:
                res = subprocess.run(
                    cmd,
                    cwd=workspace_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=settings.TOOL_TIMEOUT_SECONDS
                )
                if res.returncode == 0:
                    return {
                        "status": "success",
                        "file": file_path,
                        "tool": "node --check",
                        "violation_count": 0,
                        "violations": [],
                        "raw_output": "Syntax validation passed."
                    }
                else:
                    return {
                        "status": "success",
                        "file": file_path,
                        "tool": "node --check",
                        "violation_count": 1,
                        "violations": [{
                            "file": file_path,
                            "line": 1,
                            "col": 1,
                            "message": res.stderr.strip()
                        }],
                        "raw_output": res.stderr.strip()
                    }
            except Exception as e:
                return {"status": "error", "file": file_path, "error": str(e), "violations": []}

    return {
        "status": "unsupported",
        "file": file_path,
        "message": f"No linter configured for {ext}",
        "violations": []
    }
