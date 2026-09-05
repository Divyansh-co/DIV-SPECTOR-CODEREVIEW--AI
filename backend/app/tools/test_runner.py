import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any
from app.config import settings

def run_tests(test_path: str, workspace_root: str) -> Dict[str, Any]:
    """
    Runs pytest or jest in a restricted subprocess with a strict timeout
    and isolated environment.
    """
    full_path = Path(workspace_root) / test_path
    if not full_path.exists():
        return {
            "status": "error",
            "test_path": test_path,
            "error": f"Test path does not exist: {test_path}"
        }

    # Sandboxed environment - stripped of dangerous parent env tokens
    restricted_env = {
        "PATH": os.environ.get("PATH", ""),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "PYTHONPATH": workspace_root,
        "PYTHONDONTWRITEBYTECODE": "1"
    }

    if full_path.suffix == ".py" or full_path.is_dir():
        cmd = [
            sys.executable, "-m", "pytest",
            "-q", "--tb=short",
            str(full_path)
        ]
        try:
            res = subprocess.run(
                cmd,
                cwd=workspace_root,
                env=restricted_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=settings.TOOL_TIMEOUT_SECONDS
            )
            passed = res.returncode == 0
            output = (res.stdout + "\n" + res.stderr).strip()
            return {
                "status": "success",
                "framework": "pytest",
                "passed": passed,
                "exit_code": res.returncode,
                "test_path": test_path,
                "output": output or ("All tests passed." if passed else "Tests failed.")
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "framework": "pytest",
                "passed": False,
                "test_path": test_path,
                "error": f"Test execution timed out after {settings.TOOL_TIMEOUT_SECONDS}s (sandbox guardrail)"
            }
        except Exception as e:
            return {
                "status": "error",
                "test_path": test_path,
                "error": str(e)
            }

    return {
        "status": "unsupported",
        "test_path": test_path,
        "message": f"Unsupported test file extension: {full_path.suffix}"
    }
