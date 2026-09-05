import ast
import re
from typing import List, Dict, Any, Optional

def chunk_python_code(file_path: str, code: str) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    lines = code.splitlines()

    try:
        tree = ast.parse(code, filename=file_path)
    except SyntaxError:
        # Fallback to single chunk if syntax is broken
        return [{
            "id": f"{file_path}:1-{len(lines)}",
            "file_path": file_path,
            "unit_type": "file",
            "name": file_path,
            "start_line": 1,
            "end_line": len(lines),
            "content": code,
            "language": "python",
            "docstring": None
        }]

    # Collect classes and functions
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start + len(ast.unparse(node).splitlines()))
            docstring = ast.get_docstring(node)
            chunk_content = "\n".join(lines[start - 1:end])
            chunks.append({
                "id": f"{file_path}:{node.name}:{start}-{end}",
                "file_path": file_path,
                "unit_type": "function",
                "name": node.name,
                "start_line": start,
                "end_line": end,
                "content": chunk_content,
                "language": "python",
                "docstring": docstring
            })
        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start + len(ast.unparse(node).splitlines()))
            docstring = ast.get_docstring(node)
            chunk_content = "\n".join(lines[start - 1:end])
            chunks.append({
                "id": f"{file_path}:{node.name}:{start}-{end}",
                "file_path": file_path,
                "unit_type": "class",
                "name": node.name,
                "start_line": start,
                "end_line": end,
                "content": chunk_content,
                "language": "python",
                "docstring": docstring
            })
            # Also extract methods inside the class for fine-grained retrieval
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_start = item.lineno
                    m_end = getattr(item, "end_lineno", m_start + len(ast.unparse(item).splitlines()))
                    m_doc = ast.get_docstring(item)
                    m_content = "\n".join(lines[m_start - 1:m_end])
                    chunks.append({
                        "id": f"{file_path}:{node.name}.{item.name}:{m_start}-{m_end}",
                        "file_path": file_path,
                        "unit_type": "method",
                        "name": f"{node.name}.{item.name}",
                        "start_line": m_start,
                        "end_line": m_end,
                        "content": m_content,
                        "language": "python",
                        "docstring": m_doc
                    })

    # If no functions/classes found (e.g. script), chunk entire file
    if not chunks:
        chunks.append({
            "id": f"{file_path}:1-{len(lines)}",
            "file_path": file_path,
            "unit_type": "module",
            "name": file_path,
            "start_line": 1,
            "end_line": max(len(lines), 1),
            "content": code,
            "language": "python",
            "docstring": None
        })

    return chunks

def chunk_js_ts_code(file_path: str, code: str, language: str = "javascript") -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    lines = code.splitlines()

    # Pattern for functions, arrow functions, and classes
    fn_patterns = [
        # function foo(...) {
        (re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\("), "function"),
        # const/let/var foo = (...) => { or function(...) {
        (re.compile(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>"), "function"),
        # class Foo {
        (re.compile(r"^(?:export\s+)?class\s+([A-Za-z0-9_$]+)"), "class"),
    ]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        matched = False

        for pat, u_type in fn_patterns:
            m = pat.search(line)
            if m:
                name = m.group(1)
                start_line = i + 1
                # Track braces to find the end of block
                open_braces = 0
                found_brace = False
                end_line = start_line

                for j in range(i, len(lines)):
                    cur_line = lines[j]
                    for char in cur_line:
                        if char == "{":
                            open_braces += 1
                            found_brace = True
                        elif char == "}":
                            open_braces -= 1

                    if found_brace and open_braces <= 0:
                        end_line = j + 1
                        break
                else:
                    end_line = min(i + 40, len(lines))

                chunk_content = "\n".join(lines[start_line - 1:end_line])
                chunks.append({
                    "id": f"{file_path}:{name}:{start_line}-{end_line}",
                    "file_path": file_path,
                    "unit_type": u_type,
                    "name": name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": chunk_content,
                    "language": language,
                    "docstring": None
                })
                i = max(i, end_line - 1)
                matched = True
                break

        i += 1

    if not chunks:
        chunks.append({
            "id": f"{file_path}:1-{len(lines)}",
            "file_path": file_path,
            "unit_type": "module",
            "name": file_path,
            "start_line": 1,
            "end_line": max(len(lines), 1),
            "content": code,
            "language": language,
            "docstring": None
        })

    return chunks

def chunk_file(file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    path = file_info["path"]
    lang = file_info.get("language", "python")
    content = file_info.get("content", "")

    if lang == "python":
        return chunk_python_code(path, content)
    elif lang in ("javascript", "typescript"):
        return chunk_js_ts_code(path, content, lang)
    else:
        lines = content.splitlines()
        return [{
            "id": f"{path}:1-{len(lines)}",
            "file_path": path,
            "unit_type": "file",
            "name": path,
            "start_line": 1,
            "end_line": max(len(lines), 1),
            "content": content,
            "language": lang,
            "docstring": None
        }]
