import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.retrieval.vector_store import LocalVectorStore
from app.retrieval.dependency_graph import DependencyGraph
from app.tools.linter import run_linter
from app.tools.test_runner import run_tests
from app.tools.static_analyzer import get_function_callers

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Semantic search over the indexed codebase vector store to locate relevant classes, functions, or patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g. 'authentication token verification' or 'database query execution')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a specific file in the workspace with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file to read (e.g. 'backend/app/auth.py')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_linter",
            "description": "Run the linter (flake8 for Python or syntax check for JS/TS) on a given file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file to lint"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Execute pytest or test suite on a specific test file or test directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the test file or test directory"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_function_callers",
            "description": "Perform AST static analysis to find all files and lines that invoke a given function.",
            "parameters": {
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function to trace callers for"
                    }
                },
                "required": ["function_name"]
            }
        }
    }
]

class ToolExecutor:
    def __init__(
        self,
        workspace_root: str,
        vector_store: LocalVectorStore,
        dep_graph: DependencyGraph
    ):
        self.workspace_root = Path(workspace_root)
        self.vector_store = vector_store
        self.dep_graph = dep_graph

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        status = "success"
        output: Any = ""

        try:
            if tool_name == "search_codebase":
                query = arguments.get("query", "")
                results = self.vector_store.search(query, top_k=5)
                # Format results compactly for the LLM
                formatted = []
                for r in results:
                    formatted.append({
                        "file": r.get("file_path"),
                        "unit": f"{r.get('unit_type')} {r.get('name')}",
                        "lines": f"{r.get('start_line')}-{r.get('end_line')}",
                        "snippet": r.get("content", "")[:350]
                    })
                output = json.dumps(formatted, indent=2)

            elif tool_name == "read_file":
                rel_path = arguments.get("path", "")
                full_path = self.workspace_root / rel_path
                if not full_path.exists():
                    output = f"Error: File not found: {rel_path}"
                    status = "error"
                else:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    annotated = [f"{i+1:4d} | {line}" for i, line in enumerate(lines[:500])]
                    output = "".join(annotated)

            elif tool_name == "run_linter":
                rel_path = arguments.get("path", "")
                res = run_linter(rel_path, str(self.workspace_root))
                output = json.dumps(res, indent=2)
                if res.get("status") in ("error", "timeout"):
                    status = res.get("status")

            elif tool_name == "run_tests":
                rel_path = arguments.get("path", "")
                res = run_tests(rel_path, str(self.workspace_root))
                output = json.dumps(res, indent=2)
                if res.get("status") in ("error", "timeout"):
                    status = res.get("status")

            elif tool_name == "get_function_callers":
                fn_name = arguments.get("function_name", "")
                res = get_function_callers(fn_name, self.dep_graph)
                output = json.dumps(res, indent=2)

            else:
                output = f"Error: Unknown tool {tool_name}"
                status = "error"

        except Exception as e:
            output = f"Tool execution failed with exception: {str(e)}"
            status = "error"

        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "tool_name": tool_name,
            "tool_input": arguments,
            "tool_output": str(output),
            "duration_ms": duration_ms,
            "status": status
        }
