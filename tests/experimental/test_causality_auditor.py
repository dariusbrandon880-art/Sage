from __future__ import annotations

import json
import tempfile
from pathlib import Path

from sage.experimental.causality_auditor import DecisionCausalityAuditor


def test_basic_lineage_and_evidence(tmp_path: Path):
    # Setup workspace layout
    ws = tmp_path / "workspace"
    comp = ws / "compliance"
    ev = ws / "evidence_capture"
    comp.mkdir(parents=True)
    ev.mkdir(parents=True)

    # Create a parent node and child node in HDG
    parent = {
        "node_id": "node_parent",
        "description": "Parent node",
        "parent_ids": [],
        "evidence_refs": ["ev_parent.txt"],
        "validation_score": 0.9,
        "contradictions": [],
        "is_promoted": False,
        "metadata": {},
    }
    child = {
        "node_id": "node_child",
        "description": "Child node",
        "parent_ids": ["node_parent"],
        "evidence_refs": ["ev_child.txt"],
        "validation_score": 0.95,
        "contradictions": [],
        "is_promoted": False,
        "metadata": {},
    }
    hdg = [parent, child]
    hdg_path = comp / "hdg_causality.json"
    hdg_path.write_text(json.dumps(hdg))

    # Create spek vault with a receipt for the child
    vault = [
        {
            "receipt_id": "r1",
            "proposal_id": "node_child",
            "timestamp": "2026-01-01T00:00:00Z",
            "lifecycle_state": "VALIDATED",
            "execution_permission": True,
            "authority_integrity_score": 0.99,
            "hdg_trace": [{"node_id": "node_parent"}, {"node_id": "node_child"}],
            "attestation_signature": "sig",
            "receipt_hash": "h",
            "previous_receipt_hash": "p",
        }
    ]
    vault_path = comp / "spek_vault.json"
    vault_path.write_text(json.dumps(vault))

    # Create evidence files for parent and child
    (ev / "ev_parent.txt").write_text("parent evidence")
    (ev / "ev_child.txt").write_text("child evidence")

    # Record mtimes/content to assert immutability later
    before_hdg = hdg_path.read_text()
    before_vault = vault_path.read_text()

    auditor = DecisionCausalityAuditor(workspace=ws)
    report = auditor.audit("node_child")

    assert report["decision_id"] == "node_child"

    # no HDG or evidence issues
    codes = [i["code"] for i in report["issues"]]
    assert "MISSING_HDG_NODE" not in codes
    assert "MISSING_EVIDENCE" not in codes

    # lineage should include both nodes deterministically sorted
    node_ids = [n["node_id"] for n in report["lineage"]]
    assert set(node_ids) == {"node_parent", "node_child"}

    # evidence existence reported
    ev_refs = {e["ref"]: e["exists"] for e in report["evidence"]}
    assert ev_refs.get("ev_parent.txt") is True
    assert ev_refs.get("ev_child.txt") is True

    # receipt present
    assert any(r.get("proposal_id") == "node_child" for r in report["receipts"]) is True

    # immutability: files unchanged
    assert hdg_path.read_text() == before_hdg
    assert vault_path.read_text() == before_vault


def test_missing_parent_and_evidence(tmp_path: Path):
    ws = tmp_path / "workspace"
    comp = ws / "compliance"
    ev = ws / "evidence_capture"
    comp.mkdir(parents=True)
    ev.mkdir(parents=True)

    # Child node references missing parent and missing evidence
    child = {
        "node_id": "orphan_child",
        "description": "Orphan child",
        "parent_ids": ["no_such_parent"],
        "evidence_refs": ["missing_ev.txt"],
        "validation_score": 0.5,
        "contradictions": [],
        "is_promoted": False,
        "metadata": {},
    }
    hdg_path = comp / "hdg_causality.json"
    hdg_path.write_text(json.dumps([child]))

    vault_path = comp / "spek_vault.json"
    vault_path.write_text(json.dumps([]))

    auditor = DecisionCausalityAuditor(workspace=ws)
    report = auditor.audit("orphan_child")

    codes = {i["code"] for i in report["issues"]}
    assert "MISSING_HDG_PARENT" in codes
    assert "MISSING_EVIDENCE" in codes

    # evidence existence false
    ev_refs = {e["ref"]: e["exists"] for e in report["evidence"]}
    assert ev_refs.get("missing_ev.txt") is False
