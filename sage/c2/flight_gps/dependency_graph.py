"""Static dependency extraction for Flight GPS collision analysis."""

import ast
from typing import Dict, Set


class DependencyGraphAnalyzer:
    """Extract symbols and direct import/module dependencies from Python source."""

    def extract(self, file_content: str) -> Dict[str, Set[str]]:
        tree = ast.parse(file_content)
        symbols: Set[str] = set()
        modules: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.add(node.name)
            elif isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
        return {"symbols": symbols, "modules": modules}
