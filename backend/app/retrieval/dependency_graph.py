import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

class DependencyGraph:
    def __init__(self):
        # file_path -> set of imported modules/files
        self.file_imports: Dict[str, Set[str]] = {}
        # file_path -> set of files that import this file
        self.reverse_imports: Dict[str, Set[str]] = {}
        # function_name -> list of {file, line, caller_name}
        self.function_callers: Dict[str, List[Dict[str, Any]]] = {}
        # file_path -> list of function names defined in it
        self.file_definitions: Dict[str, Set[str]] = {}
        # file_path -> list of test files associated
        self.test_mappings: Dict[str, List[str]] = {}

    def build_from_files(self, scanned_files: List[Dict[str, Any]]):
        for f in scanned_files:
            path = f["path"]
            lang = f.get("language", "")
            content = f.get("content", "")

            self.file_imports[path] = set()
            self.file_definitions[path] = set()

            if lang == "python":
                self._parse_python(path, content)
            elif lang in ("javascript", "typescript"):
                self._parse_js_ts(path, content)

        # Build reverse imports
        for f_path in self.file_imports:
            self.reverse_imports[f_path] = set()

        for source_file, targets in self.file_imports.items():
            for target in targets:
                # Match target against known file paths
                for candidate in self.file_imports:
                    if target in candidate or candidate.replace(".py", "").endswith(target.replace(".", "/")):
                        self.reverse_imports[candidate].add(source_file)

        # Map test files
        all_paths = list(self.file_imports.keys())
        test_files = [p for p in all_paths if "test" in p.lower() or "spec" in p.lower()]

        for path in all_paths:
            stem = Path(path).stem.lower().replace("_test", "").replace(".test", "").replace(".spec", "")
            matches = []
            for tf in test_files:
                if stem in tf.lower() and tf != path:
                    matches.append(tf)
            self.test_mappings[path] = matches

    def _parse_python(self, path: str, content: str):
        try:
            tree = ast.parse(content, filename=path)
        except Exception:
            return

        current_func = "module"

        class Visitor(ast.NodeVisitor):
            def __init__(self, outer):
                self.outer = outer
                self.func_stack = ["<module>"]

            def visit_Import(self, node):
                for alias in node.names:
                    self.outer.file_imports[path].add(alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                mod = node.module or ""
                self.outer.file_imports[path].add(mod)
                for alias in node.names:
                    self.outer.file_imports[path].add(f"{mod}.{alias.name}" if mod else alias.name)
                self.generic_visit(node)

            def visit_FunctionDef(self, node):
                self.outer.file_definitions[path].add(node.name)
                self.func_stack.append(node.name)
                self.generic_visit(node)
                self.func_stack.pop()

            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)

            def visit_Call(self, node):
                caller = self.func_stack[-1] if self.func_stack else "<module>"
                fn_name = None
                if isinstance(node.func, ast.Name):
                    fn_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fn_name = node.func.attr

                if fn_name:
                    if fn_name not in self.outer.function_callers:
                        self.outer.function_callers[fn_name] = []
                    self.outer.function_callers[fn_name].append({
                        "file_path": path,
                        "line_number": getattr(node, "lineno", 1),
                        "caller_function": caller
                    })
                self.generic_visit(node)

        Visitor(self).visit(tree)

    def _parse_js_ts(self, path: str, content: str):
        # Regex for imports: import ... from '...'; or const ... = require('...')
        import_pat = re.compile(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""")
        for m in import_pat.finditer(content):
            target = m.group(1) or m.group(2)
            if target:
                self.file_imports[path].add(target)

        # Regex for function declarations
        fn_decl = re.compile(r"""(?:function\s+([A-Za-z0-9_$]+)|(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\()""")
        for m in fn_decl.finditer(content):
            name = m.group(1) or m.group(2)
            if name:
                self.file_definitions[path].add(name)

        # Regex for calls: identifier(...)
        call_pat = re.compile(r"""\b([A-Za-z0-9_$]+)\s*\(""")
        for lineno, line in enumerate(content.splitlines(), start=1):
            for m in call_pat.finditer(line):
                fn_name = m.group(1)
                # Filter out standard keywords
                if fn_name in ("if", "for", "while", "switch", "catch", "import", "require", "return"):
                    continue
                if fn_name not in self.function_callers:
                    self.function_callers[fn_name] = []
                self.function_callers[fn_name].append({
                    "file_path": path,
                    "line_number": lineno,
                    "caller_function": "<scope>"
                })

    def get_callers(self, function_name: str) -> List[Dict[str, Any]]:
        return self.function_callers.get(function_name, [])

    def get_diff_context(self, changed_files: List[str], changed_functions: List[str]) -> Dict[str, Any]:
        """
        Retrieves callers of changed functions, imported modules, 
        reverse-dependent files, and test files for the diff.
        """
        callers: Dict[str, List[Dict[str, Any]]] = {}
        for fn in changed_functions:
            callers[fn] = self.get_callers(fn)

        related_tests: Set[str] = set()
        depended_by: Set[str] = set()
        imports: Set[str] = set()

        for f in changed_files:
            if f in self.test_mappings:
                related_tests.update(self.test_mappings[f])
            if f in self.reverse_imports:
                depended_by.update(self.reverse_imports[f])
            if f in self.file_imports:
                imports.update(self.file_imports[f])

        return {
            "changed_function_callers": callers,
            "dependent_files": sorted(list(depended_by)),
            "imported_modules": sorted(list(imports)),
            "relevant_test_files": sorted(list(related_tests))
        }
