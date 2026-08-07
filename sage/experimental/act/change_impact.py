"""SAGE Change-Impact & Revalidation Analyzer (SAGE-CIRA).

Analyzes the cascading validation impact of capability changes across SAGE
dependent capabilities, evidence records, and verification claims.
"""

from typing import Any, Dict, List, Set
from sage.experimental.act.capability_passport import CapabilityPassport


class SAGEChangeImpactAnalyzer:
    """Read-only analyzer to evaluate cascading capability change impacts."""

    def __init__(self, passports: List[CapabilityPassport]):
        self.passports = {p.name: p for p in passports}

    def analyze_impact(self, changed_capability_name: str) -> Dict[str, Any]:
        """Deterministically evaluates dependencies, evidence, and claims affected by a change.

        Marks affected items as:
        - REVALIDATION_REQUIRED: Direct or transitive dependent capabilities and their linked evidence.
        - UNAFFECTED: No direct or transitive dependency relationship found.
        - UNKNOWN_DEPENDENCY: Specified changed capability is missing/not present in the passport registry.
        """
        if changed_capability_name not in self.passports:
            return {
                "changed_capability": changed_capability_name,
                "status": "UNKNOWN_DEPENDENCY",
                "reason": f"Capability '{changed_capability_name}' is not registered in the passport registry.",
                "impacted_capabilities_count": 0,
                "revalidation_required_files_count": 0,
                "revalidation_required_files": [],
                "assessments": {}
            }

        # Compute direct and transitive dependencies (BFS/DFS traversal of the dependency tree)
        impacted_capabilities: Dict[str, Dict[str, Any]] = {}
        revalidation_required_files: Set[str] = set()

        # Queue for traversal, starting with direct dependents of changed_capability_name
        queue: List[str] = []
        visited: Set[str] = {changed_capability_name}

        # Find direct dependents
        for name, p in self.passports.items():
            if changed_capability_name in p.dependencies:
                queue.append(name)
                visited.add(name)
                impacted_capabilities[name] = {
                    "impact_tier": "DIRECT",
                    "provenance": f"Directly depends on changed capability '{changed_capability_name}'"
                }
                if p.evidence_path:
                    revalidation_required_files.add(p.evidence_path)

        # Transitive dependents traversal
        while queue:
            current = queue.pop(0)
            for name, p in self.passports.items():
                if name not in visited and current in p.dependencies:
                    queue.append(name)
                    visited.add(name)
                    impacted_capabilities[name] = {
                        "impact_tier": "TRANSITIVE",
                        "provenance": f"Transitively depends on changed capability '{changed_capability_name}' via '{current}'"
                    }
                    if p.evidence_path:
                        revalidation_required_files.add(p.evidence_path)

        # Build final report
        assessments: Dict[str, Dict[str, Any]] = {}
        for name, p in self.passports.items():
            if name == changed_capability_name:
                assessments[name] = {
                    "status": "CHANGED_ORIGIN",
                    "reason": "This is the source of the capability changes."
                }
            elif name in impacted_capabilities:
                assessments[name] = {
                    "status": "REVALIDATION_REQUIRED",
                    "impact_tier": impacted_capabilities[name]["impact_tier"],
                    "provenance": impacted_capabilities[name]["provenance"]
                }
            else:
                assessments[name] = {
                    "status": "UNAFFECTED",
                    "reason": f"No direct or transitive dependency on '{changed_capability_name}' exists."
                }

        return {
            "changed_capability": changed_capability_name,
            "status": "ANALYZED",
            "impacted_capabilities_count": len(impacted_capabilities),
            "revalidation_required_files_count": len(revalidation_required_files),
            "revalidation_required_files": sorted(list(revalidation_required_files)),
            "assessments": assessments
        }
