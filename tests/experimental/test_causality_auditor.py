from __future__ import annotations

import json
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

    # receipt present and annotated as not verified
    assert any(r.get("proposal_id") == "node_child" and r.get("receipt_verified") is False for r in report["receipts"]) is True

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


def test_hdg_engine_failure_fallback_and_annotation(tmp_path: Path):
    """Simulate HDG integrity failure via circular parents to force engine to fail-closed.

    Verify the auditor records HDG_LOAD_FAILURE and annotates lineage nodes as unvalidated.
    """
    ws = tmp_path / "workspace"
    comp = ws / "compliance"
    comp.mkdir(parents=True)

    # Create two nodes that reference each other -> cycle
    a = {"node_id": "a", "description": "A", "parent_ids": ["b"], "evidence_refs": ["ea.txt"], "validation_score": 1.0, "contradictions": [], "is_promoted": False, "metadata": {}}
    b = {"node_id": "b", "description": "B", "parent_ids": ["a"], "evidence_refs": ["eb.txt"], "validation_score": 1.0, "contradictions": [], "is_promoted": False, "metadata": {}}
    comp.joinpath("hdg_causality.json").write_text(json.dumps([a, b]))

    # No spek vault
    comp.joinpath("spek_vault.json").write_text(json.dumps([]))

    auditor = DecisionCausalityAuditor(workspace=ws)
    report = auditor.audit("a")

    # Should record HDG_LOAD_FAILURE when engine fails integrity checks
    codes = {i["code"] for i in report["issues"]}
    assert "HDG_LOAD_FAILURE" in codes

    # Lineage nodes should be annotated as UNVERIFIED_RAW_HDG
    for node in report.get("lineage", []):
        assert node.get("_validation_status") == "UNVERIFIED_RAW_HDG"


def test_deterministic_serialization_and_duplicates(tmp_path: Path):
    ws = tmp_path / "workspace"
    comp = ws / "compliance"
    ev = ws / "evidence_capture"
    comp.mkdir(parents=True)
    ev.mkdir(parents=True)

    # Node with two parents and duplicate evidence refs
    p1 = {"node_id": "p1", "description": "P1", "parent_ids": [], "evidence_refs": ["x.txt"], "validation_score": 1.0, "contradictions": [], "is_promoted": False, "metadata": {}}
    p2 = {"node_id": "p2", "description": "P2", "parent_ids": [], "evidence_refs": ["x.txt"], "validation_score": 1.0, "contradictions": [], "is_promoted": False, "metadata": {}}
    child = {"node_id": "child", "description": "C", "parent_ids": ["p1", "p2"], "evidence_refs": ["x.txt", "y.txt"], "validation_score": 1.0, "contradictions": [], "is_promoted": False, "metadata": {}}
    comp.joinpath("hdg_causality.json").write_text(json.dumps([p1, p2, child]))

    # Create spek vault with duplicate receipts referencing same proposal_id
    vault = [
        {"receipt_id": "rdup1", "proposal_id": "child", "lifecycle_state": "VALIDATED", "hdg_trace": [{"node_id": "p1"}, {"node_id": "child"}]},
        {"receipt_id": "rdup1", "proposal_id": "child", "lifecycle_state": "VALIDATED", "hdg_trace": [{"node_id": "p1"}, {"node_id": "child"}]},
    ]
    comp.joinpath("spek_vault.json").write_text(json.dumps(vault))

    # Create evidence files
    (ev / "x.txt").write_text("x")
    (ev / "y.txt").write_text("y")

    auditor = DecisionCausalityAuditor(workspace=ws)
    report1 = auditor.audit("child")
    ser1 = auditor.serialize(report1)
    report2 = auditor.audit("child")
    ser2 = auditor.serialize(report2)

    # Deterministic serialized output
    assert ser1 == ser2

    # Duplicate evidence should be deduped in evidence list
    refs = [e["ref"] for e in report1.get("evidence", [])]
    assert refs.count("x.txt") == 1

    # Duplicate receipts deduped by receipt_id
    rids = [r["receipt_id"] for r in report1.get("receipts", [])]
    assert rids.count("rdup1") == 1
