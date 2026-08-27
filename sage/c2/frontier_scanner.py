"""Static frontier analysis for bounded SAGE C2 missions.

The scanner is advisory by design: it maps Python import dependencies among
changed files so C2 can detect likely coupled frontiers before dispatching
parallel work. It does not replace Git mergeability or runtime verification.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable


class FrontierScanError(ValueError):
    """Raised when a Python source file cannot be parsed."""


def scan_python_frontier(root: str | Path, changed_files: Iterable[str | Path]) -> dict[str, set[str]]:
    """Return changed-file dependency edges discovered from local imports.

    Only local ``sage`` imports are resolved. External packages are ignored.
    The result maps each changed Python file to changed Python files it imports
    directly. A missing local module is simply omitted because the scanner is
    intended to be conservative without inventing repository state.
    """
    root_path = Path(root)
    changed = {Path(path).as_posix().lstrip("./") for path in changed_files if str(path).endswith(".py")}
    module_to_file = _module_index(root_path)
    edges: dict[str, set[str]] = {path: set() for path in changed}

    for relative in changed:
        source = root_path / relative
        if not source.is_file():
            continue
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=relative)
        except SyntaxError as exc:
            raise FrontierScanError(f"Cannot parse {relative}: {exc}") from exc
        for module in _imports(tree):
            target = module_to_file.get(module)
            if target and target in changed and target != relative:
                edges[relative].add(target)
    return edges


def overlapping_frontiers(frontiers: dict[str, Iterable[str]]) -> set[tuple[str, str]]:
    """Return pairs of flight IDs whose declared path sets overlap."""
    normalized = {name: {Path(path).as_posix().lstrip("./") for path in paths} for name, paths in frontiers.items()}
    overlaps: set[tuple[str, str]] = set()
    names = sorted(normalized)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            if normalized[left] & normalized[right]:
                overlaps.add((left, right))
    return overlaps


def _module_index(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in root.rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        parts = relative[:-3].split("/")
        if parts[-1] == "__init__":
            parts.pop()
        module = ".".join(parts)
        result[module] = relative
    return result


def _imports(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names if alias.name.startswith("sage."))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("sage."):
            modules.add(node.module)
    return modules
