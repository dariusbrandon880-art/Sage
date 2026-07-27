import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ArchitectureMap:
    """Handles mapping of codebase directories to SAGE's five-tier architecture state:
    1. runtime/   -> Locked Production Truth
    2. core/      -> Validated Primitives
    3. archive/   -> Append-only Canonical History
    4. evolution/ -> Staged Validated Growth
    5. lab/       -> Experimental Workspace
    """

    TIERS = {
        "runtime": ["sage/runtime"],
        "core": ["sage/core"],
        "archive": ["Main Archive", "sage/archive"],
        "evolution": ["sage/evolution"],
        "lab": ["sage/lab"]
    }

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def determine_file_tier(self, relative_path: str) -> str:
        """Map a relative path to its corresponding architecture tier."""
        p_str = relative_path.replace("\\", "/")
        for tier, prefixes in self.TIERS.items():
            for prefix in prefixes:
                if p_str.startswith(prefix):
                    return tier
        return "external"

    def verify_one_way_import_law(self) -> Tuple[bool, List[str]]:
        """Scans all Python files in the workspace using AST analysis.
        Enforces that production tiers (runtime, core, archive) MUST NOT
        import anything from experimental/lab tiers (lab, evolution).

        Returns:
            (is_compliant, violations_list)
        """
        violations = []
        protected_prefixes = ["sage.lab", "sage.evolution"]
        # Look for files under sage/runtime, sage/core, sage/archive
        target_dirs = [
            self.workspace_root / "sage" / "runtime",
            self.workspace_root / "sage" / "core",
            self.workspace_root / "sage" / "archive",
        ]

        for d in target_dirs:
            if not d.exists():
                continue
            for file_path in d.rglob("*.py"):
                rel_path = file_path.relative_to(self.workspace_root)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        node = ast.parse(f.read(), filename=str(rel_path))
                except Exception as e:
                    # Non-parseable code can be ignored or logged
                    continue

                for child in ast.walk(node):
                    if isinstance(child, ast.Import):
                        for name in child.names:
                            for bad_prefix in protected_prefixes:
                                if name.name == bad_prefix or name.name.startswith(bad_prefix + "."):
                                    violations.append(
                                        f"Violation in {rel_path}: Illegal direct import '{name.name}'"
                                    )
                    elif isinstance(child, ast.ImportFrom):
                        module_name = child.module
                        if module_name:
                            for bad_prefix in protected_prefixes:
                                if module_name == bad_prefix or module_name.startswith(bad_prefix + "."):
                                    violations.append(
                                        f"Violation in {rel_path}: Illegal from-import from '{module_name}'"
                                    )

        return len(violations) == 0, violations
