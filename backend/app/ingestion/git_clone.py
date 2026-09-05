import os
import shutil
import subprocess
from pathlib import Path
from app.config import settings

def clone_repository(repo_url: str, job_id: str) -> Path:
    """
    Clones git repository into sandboxed workspace storage folder.
    """
    target_dir = settings.STORAGE_DIR / job_id
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["git", "clone", "--depth", "1", repo_url, str(target_dir)]
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45,
            check=True
        )
        return target_dir
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 45 seconds")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git clone failed: {e.stderr or e.stdout}")

def extract_git_diff(repo_dir: Path, base_ref: str, head_ref: str) -> str:
    """
    Generates git diff between two references in a cloned repo.
    """
    cmd = ["git", "diff", f"{base_ref}..{head_ref}"]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            check=True
        )
        return result.stdout
    except Exception as e:
        raise RuntimeError(f"Failed to generate git diff: {e}")
