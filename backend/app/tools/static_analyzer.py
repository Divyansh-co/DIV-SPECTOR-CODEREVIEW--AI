from typing import List, Dict, Any
from app.retrieval.dependency_graph import DependencyGraph

def get_function_callers(function_name: str, dep_graph: DependencyGraph) -> Dict[str, Any]:
    """
    Returns all detected callers of a target function name via AST static analysis.
    """
    callers = dep_graph.get_callers(function_name)
    return {
        "function_name": function_name,
        "caller_count": len(callers),
        "callers": callers
    }
