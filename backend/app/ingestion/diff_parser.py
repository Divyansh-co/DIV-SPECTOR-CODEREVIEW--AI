import re
from typing import List, Dict, Any

HUNK_HEADER_REGEX = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

def parse_git_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parses unified git diff into structured file changes and hunk ranges.
    """
    if not diff_text or not diff_text.strip():
        return []

    lines = diff_text.splitlines()
    files_diff: List[Dict[str, Any]] = []
    current_file: Dict[str, Any] = None
    current_hunk: Dict[str, Any] = None
    new_line_num = 0

    for line in lines:
        if line.startswith("diff --git"):
            if current_file:
                if current_hunk:
                    current_file["hunks"].append(current_hunk)
                    current_hunk = None
                files_diff.append(current_file)

            parts = line.split()
            # typical: diff --git a/path/to/file.py b/path/to/file.py
            b_path = parts[-1].lstrip("b/") if len(parts) >= 4 else "unknown"
            current_file = {
                "file_path": b_path,
                "hunks": [],
                "added_lines": [],
                "modified_line_numbers": []
            }
            continue

        if line.startswith("+++ b/"):
            if current_file:
                current_file["file_path"] = line[6:].strip()
            continue

        hunk_match = HUNK_HEADER_REGEX.match(line)
        if hunk_match:
            if current_hunk and current_file:
                current_file["hunks"].append(current_hunk)

            new_start = int(hunk_match.group(3))
            new_line_num = new_start
            current_hunk = {
                "header": line,
                "new_start": new_start,
                "lines": [],
                "changed_line_numbers": []
            }
            continue

        if current_hunk:
            current_hunk["lines"].append(line)
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk["changed_line_numbers"].append(new_line_num)
                if current_file:
                    current_file["modified_line_numbers"].append(new_line_num)
                    current_file["added_lines"].append({
                        "line_number": new_line_num,
                        "content": line[1:]
                    })
                new_line_num += 1
            elif line.startswith("-") and not line.startswith("---"):
                pass  # deleted line in old version
            else:
                new_line_num += 1

    if current_file:
        if current_hunk:
            current_file["hunks"].append(current_hunk)
        files_diff.append(current_file)

    return files_diff
