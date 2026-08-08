from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

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

    def _load_spek_vault(self) -> List[Dict[str, Any]]:
        if not self.spek_vault_path.exists():
            return []
        try:
            with open(self.spek_vault_path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def _node_to_dict(self, node) -> Dict[str, Any]:
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

    def _load_raw_hdg(self) -> Dict[str, Dict[str, Any]]:
        """Fallback loader that reads the HDG JSON file directly without enforcing integrity.

        Returns a mapping of node_id -> raw node dicts. This is used when HDGEngine fails to load
        (e.g., fail-closed on integrity errors) so the auditor can still report missing parents/evidence
        non-destructively. Nodes returned from this function are annotated as unvalidated.
        """
        if not self.hdg_path.exists():
            return {}
        try:
            raw = json.loads(self.hdg_path.read_text())
            if not isinstance(raw, list):
                return {}
            mapping: Dict[str, Dict[str, Any]] = {}
            for item in raw:
                if not isinstance(item, dict):
                    continue
                nid = item.get("node_id")
                if not nid:
                    continue
                # Mark as unvalidated raw HDG node so consumers cannot mistake it for validated data
                item_copy = dict(item)
                item_copy["_validation_status"] = "UNVERIFIED_RAW_HDG"
                mapping[nid] = item_copy
            return mapping
        except Exception:
            return {}

    def serialize(self, report: Dict[str, Any]) -> str:
        """Return a canonical, deterministic JSON serialization of the report.

        Use sort_keys=True and compact separators to ensure byte-for-byte determinism
        when the same in-memory report is serialized repeatedly.
        """
        return json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def audit(self, decision_id: str) -> Dict[str, Any]:
        """Run a read-only audit for the given decision/proposal/node id.

        Returns a machine-readable report with the following top-level keys:
        - decision_id: str
        - issues: List[Dict(code, message, details)]
        - lineage: List[Dict] ordered from root ancestors -> decision (deterministic)
        - evidence: List[Dict(ref, exists, integrity_verified=False)]
        - receipts: List[Dict(receipt_id, proposal_id, lifecycle_state, hdg_trace, receipt_verified=False)]
        - hdg_engine_loaded: bool
        """
        report: Dict[str, Any] = {
            "decision_id": decision_id,
            "issues": [],
            "lineage": [],
            "evidence": [],
            "receipts": [],
            "hdg_engine_loaded": True,
        }

        # 1) Load HDG read-only via existing engine (do not call any mutating APIs). If HDGEngine
        # fails closed due to integrity problems, record the failure and fall back to raw JSON
        # inspection to report missing parents/evidence conservatively.
        hdg_nodes: Dict[str, Any] = {}
        try:
            hdg = HDGEngine(storage_path=self.hdg_path)
            # Use authoritative engine semantics for ancestry collection
            if decision_id in hdg.nodes:
                try:
                    ancestors = hdg._get_ancestors(decision_id)
                except Exception:
                    # Fallback: build ancestors by visiting nodes reachable via parent links
                    ancestors = set()
                    stack = [decision_id]
                    while stack:
                        nid = stack.pop()
                        if nid in ancestors:
                            continue
                        ancestors.add(nid)
                        node = hdg.nodes.get(nid)
                        if node:
                            for pid in node.parent_ids:
                                if pid not in ancestors:
                                    stack.append(pid)
                # Build deterministic ordered lineage using authoritative node objects
                ordered_ids = sorted(list(ancestors))
                lineage_list: List[Dict[str, Any]] = []
                for nid in ordered_ids:
                    try:
                        node_obj = hdg.get_node(nid)
                        node_dict = self._node_to_dict(node_obj)
                        node_dict["_validation_status"] = "VALIDATED_HDG_ENGINE"
                        lineage_list.append(node_dict)
                    except Exception:
                        # If engine cannot provide node (unexpected), record missing parent
                        report["issues"].append({"code": "MISSING_HDG_PARENT", "message": "Parent node referenced but not present in HDG", "details": {"missing_node_id": nid}})
                report["lineage"] = lineage_list
                # Use engine's evidence tracing authoritative method
                try:
                    evidences = hdg.trace_evidence(decision_id)
                except Exception:
                    evidences = []
                # Add evidence entries deterministically
                for ref in sorted(evidences):
                    exists = self._evidence_exists(ref)
                    if not exists:
                        report["issues"].append({"code": "MISSING_EVIDENCE", "message": "Evidence reference missing on disk", "details": {"ref": ref}})
                    report["evidence"].append({"ref": ref, "exists": exists, "integrity_verified": False})
            else:
                report["issues"].append({"code": "MISSING_HDG_NODE", "message": "Decision node not present in HDG", "details": {"node_id": decision_id}})
        except Exception as e:
            # HDGEngine failed (failed-closed). Record the failure and fall back to raw JSON inspection.
            report["issues"].append({"code": "HDG_LOAD_FAILURE", "message": "Failed to load HDG ledger via engine; falling back to raw inspection", "details": str(e)})
            report["hdg_engine_loaded"] = False
            hdg_nodes = self._load_raw_hdg()
            # Build lineage deterministically from raw mapping keys
            if decision_id in hdg_nodes:
                lineage_nodes = {}
                stack = [decision_id]
                visited = set()
                while stack:
                    nid = stack.pop()
                    if nid in visited:
                        continue
                    visited.add(nid)
                    node = hdg_nodes.get(nid)
                    if node is None:
                        report["issues"].append({"code": "MISSING_HDG_PARENT", "message": "Parent node referenced but not present in HDG", "details": {"missing_node_id": nid}})
                        continue
                    # Node already annotated as UNVERIFIED_RAW_HDG by loader
                    lineage_nodes[nid] = node
                    for pid in sorted(node.get("parent_ids", []) or []):
                        if pid not in visited:
                            stack.append(pid)
                ordered = [lineage_nodes[k] for k in sorted(lineage_nodes.keys())]
                report["lineage"] = ordered
                # Collect evidence refs from raw lineage deterministically
                evidence_refs: List[str] = []
                for node in report["lineage"]:
                    for ref in sorted(node.get("evidence_refs", []) or []):
                        if ref not in evidence_refs:
                            evidence_refs.append(ref)
                for ref in evidence_refs:
                    exists = self._evidence_exists(ref)
                    if not exists:
                        report["issues"].append({"code": "MISSING_EVIDENCE", "message": "Evidence reference missing on disk", "details": {"ref": ref}})
                    report["evidence"].append({"ref": ref, "exists": exists, "integrity_verified": False})
            else:
                report["issues"].append({"code": "MISSING_HDG_NODE", "message": "Decision node not present in HDG (raw load)", "details": {"node_id": decision_id}})

        # 3) Search SPEK vault receipts for matching proposal/hdg trace references
        vault = self._load_spek_vault()
        seen_receipts = set()
        for r in vault:
            try:
                # match by proposal_id OR if hdg_trace references the decision
                proposal_match = (r.get("proposal_id") == decision_id)
                trace_match = any((td.get("node_id") == decision_id) for td in (r.get("hdg_trace") or []))
                if proposal_match or trace_match:
                    rid = r.get("receipt_id") or json.dumps(r, sort_keys=True)
                    if rid in seen_receipts:
                        continue
                    seen_receipts.add(rid)
                    # Normalize receipt fields and annotate verification state
                    report["receipts"].append({
                        "receipt_id": r.get("receipt_id"),
                        "proposal_id": r.get("proposal_id"),
                        "lifecycle_state": r.get("lifecycle_state"),
                        "hdg_trace": sorted(r.get("hdg_trace") or [], key=lambda x: json.dumps(x, sort_keys=True)),
                        "receipt_verified": False,
                    })
            except Exception:
                # Non-fatal; continue scanning rest
                continue

        # Deterministic ordering for receipts and evidence
        report["receipts"] = sorted(report["receipts"], key=lambda x: (x.get("proposal_id") or "", x.get("receipt_id") or ""))
        report["evidence"] = sorted(report["evidence"], key=lambda x: x.get("ref") or "")

        return report
