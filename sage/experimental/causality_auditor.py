from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from sage.core.hdg import HDGEngine


class DecisionCausalityAuditor:
    """Experimental, read-only Decision Causality & Lineage Auditor.

    Behavior and guarantees:
    - Read-only: never mutates files or runtime state.
    - Deterministic ordering in outputs (sorted lists where applicable).
    - Machine-readable dict output for programmatic consumption.
    - Non-authorizing and non-executing: reports only what can be mechanically observed.
    """

    def __init__(self, workspace: Optional[Path | str] = None) -> None:
        self.workspace = Path(workspace or ".")
        self.hdg_path = (self.workspace / "compliance" / "hdg_causality.json").resolve()
        self.spek_vault_path = (self.workspace / "compliance" / "spek_vault.json").resolve()
        # candidate evidence directories (searched in order)
        self.evidence_dirs = [
            (self.workspace / "evidence_capture").resolve(),
            (self.workspace / "sage_data" / "evidence_capture").resolve(),
        ]

    def _load_spek_vault(self) -> List[Dict]:
        if not self.spek_vault_path.exists():
            return []
        try:
            with open(self.spek_vault_path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _node_to_dict(self, node) -> Dict:
        # Pydantic models may be present; normalize to dict safely.
        try:
            return node.model_dump()  # pydantic v2
        except Exception:
            try:
                return node.dict()
            except Exception:
                # Fallback: attempt to convert attributes
                return {
                    "node_id": getattr(node, "node_id", None),
                    "description": getattr(node, "description", None),
                    "parent_ids": list(getattr(node, "parent_ids", []) or []),
                    "evidence_refs": list(getattr(node, "evidence_refs", []) or []),
                    "validation_score": getattr(node, "validation_score", None),
                    "contradictions": list(getattr(node, "contradictions", []) or []),
                }

    def _evidence_exists(self, ref: str) -> bool:
        # If ref is an absolute or relative path, check directly; otherwise search evidence dirs
        p = Path(ref)
        if p.is_absolute() and p.exists():
            return True
        # relative to workspace
        rel = (self.workspace / ref).resolve()
        if rel.exists():
            return True
        for d in self.evidence_dirs:
            cand = (d / ref).resolve()
            if cand.exists():
                return True
        return False

    def audit(self, decision_id: str) -> Dict:
        """Run a read-only audit for the given decision/proposal/node id.

        Returns a machine-readable report with the following top-level keys:
        - decision_id: str
        - issues: List[Dict(code, message, details)]
        - lineage: List[Dict] ordered from root ancestors -> decision (deterministic)
        - evidence: List[Dict(ref, exists)]
        - receipts: List[Dict(receipt_id, proposal_id, lifecycle_state, hdg_trace)]
        """
        report: Dict = {
            "decision_id": decision_id,
            "issues": [],
            "lineage": [],
            "evidence": [],
            "receipts": [],
        }

        # 1) Load HDG read-only via existing engine (do not call any mutating APIs)
        try:
            hdg = HDGEngine(storage_path=self.hdg_path)
        except Exception as e:
            report["issues"].append(
                {"code": "HDG_LOAD_FAILURE", "message": "Failed to load HDG ledger", "details": str(e)}
            )
            return report

        # 2) Ensure the node exists
        if decision_id not in hdg.nodes:
            report["issues"].append(
                {"code": "MISSING_HDG_NODE", "message": "Decision node not present in HDG", "details": {"node_id": decision_id}}
            )
            # Still attempt to find receipts referencing it
        else:
            # Build ancestor lineage deterministically by BFS from root ancestors to the node
            visited = set()
            stack = [decision_id]
            lineage_nodes = {}
            # Traverse graph collecting nodes reachable backwards (parents)
            while stack:
                nid = stack.pop()
                if nid in visited:
                    continue
                visited.add(nid)
                node = hdg.nodes.get(nid)
                if node is None:
                    # missing parent discovered
                    report["issues"].append(
                        {"code": "MISSING_HDG_PARENT", "message": "Parent node referenced but not present in HDG", "details": {"missing_node_id": nid}}
                    )
                    continue
                node_dict = self._node_to_dict(node)
                lineage_nodes[nid] = node_dict
                for pid in sorted(node_dict.get("parent_ids", []) or []):
                    if pid not in visited:
                        stack.append(pid)

            # Deterministic ordering: sort nodes by node_id ascending then construct path groups by parent relationships
            ordered = [lineage_nodes[k] for k in sorted(lineage_nodes.keys())]
            report["lineage"] = ordered

            # Evidence checks (collect unique refs)
            evidence_refs = []
            for node in report["lineage"]:
                for ref in sorted(node.get("evidence_refs", []) or []):
                    if ref not in evidence_refs:
                        evidence_refs.append(ref)
            for ref in evidence_refs:
                exists = self._evidence_exists(ref)
                if not exists:
                    report["issues"].append(
                        {"code": "MISSING_EVIDENCE", "message": "Evidence reference missing on disk", "details": {"ref": ref}}
                    )
                report["evidence"].append({"ref": ref, "exists": exists})

        # 3) Search SPEK vault receipts for matching proposal/hdg trace references
        vault = self._load_spek_vault()
        for r in vault:
            try:
                if r.get("proposal_id") == decision_id or any(
                    (td.get("node_id") == decision_id) for td in (r.get("hdg_trace") or [])
                ):
                    # Normalize receipt fields
                    report["receipts"].append(
                        {
                            "receipt_id": r.get("receipt_id"),
                            "proposal_id": r.get("proposal_id"),
                            "lifecycle_state": r.get("lifecycle_state"),
                            "hdg_trace": sorted(r.get("hdg_trace") or [], key=lambda x: json.dumps(x, sort_keys=True)),
                        }
                    )
            except Exception:
                # Non-fatal; continue scanning rest
                continue

        # Deterministic ordering for receipts and evidence
        report["receipts"] = sorted(report["receipts"], key=lambda x: (x.get("proposal_id") or "", x.get("receipt_id") or ""))
        report["evidence"] = sorted(report["evidence"], key=lambda x: x.get("ref") or "")

        return report
