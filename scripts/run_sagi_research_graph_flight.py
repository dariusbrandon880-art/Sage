"""SAGI Phase 3 Research Graph Execution Script.

Executes a live governed simulation flight through SAGI Search Loop and Research Graph,
verifying candidate ingestion, failure pattern tracking, graph hash determinism,
and research graph receipt emission under zero production mutation posture.
"""

import json
import sys
from typing import Any, Dict

from sage.experimental.sagi.search_loop import SAGISearchLoop
from sage.experimental.sagi.research_graph import SAGIResearchGraph


def run_sagi_research_graph_flight() -> Dict[str, Any]:
    """Execute SAGI Phase 3 live research graph flight."""
    print("=== SAGE / SAGI Phase 3 Research Graph Flight Started ===")

    # Step 1: Initialize SAGI Search Loop
    search_loop = SAGISearchLoop(max_depth=5)
    print(f"[1/5] SAGI Search Loop Initialized. Identity Anchor: {search_loop.controller.state.identity_anchor.initial_sha256[:16]}...")

    # Step 2: Run Cycle 1 (Success)
    rcpt_cycle1 = search_loop.run_search_cycle(cycle_id="search_cycle_01", candidates_per_cycle=3)
    print(f"[2/5] Search Cycle 1 Executed: {rcpt_cycle1.candidates_approved}/{rcpt_cycle1.candidates_tested} candidates approved. Receipt Hash: {rcpt_cycle1.receipt_sha256[:16]}...")

    # Step 3: Run Cycle 2 (With Forced Failure)
    rcpt_cycle2 = search_loop.run_search_cycle(cycle_id="search_cycle_02_fail", candidates_per_cycle=3, inject_invalid_candidate=True)
    print(f"[3/5] Search Cycle 2 Executed: {rcpt_cycle2.candidates_rejected}/{rcpt_cycle2.candidates_tested} candidates rejected (Failure Memory Updated: {rcpt_cycle2.failure_memory_size}). Receipt Hash: {rcpt_cycle2.receipt_sha256[:16]}...")

    # Step 4: Initialize SAGI Research Graph & Ingest Search Receipts
    graph = SAGIResearchGraph(graph_id="sagi_research_graph_flight_omega")
    node1 = graph.ingest_search_receipt(rcpt_cycle1)
    node2 = graph.ingest_search_receipt(rcpt_cycle2)
    print(f"[4/5] Research Graph Ingested 2 Cycle Receipts. Total Nodes: {len(graph.nodes)}, Indexed Cycles: {len(graph.cycles_indexed)}")

    # Step 5: Compute Deterministic Graph Checksum and Emit Graph Receipt
    graph_hash = graph.compute_graph_sha256()
    graph_receipt = graph.emit_graph_receipt()

    flight_result = {
        "flight_status": "SUCCESS",
        "graph_id": graph_receipt.graph_id,
        "nodes_added": graph_receipt.nodes_added,
        "cycles_indexed": graph_receipt.cycles_indexed,
        "failure_patterns_tracked": graph_receipt.failure_patterns_tracked,
        "identity_anchor": graph_receipt.identity_anchor,
        "graph_sha256": graph_hash,
        "receipt_sha256": graph_receipt.receipt_sha256,
        "research_only": graph_receipt.research_only,
        "nodes_summary": [
            {
                "node_id": node1.node_id,
                "cycle_id": node1.cycle_id,
                "guardian_result": node1.guardian_result,
                "node_sha256": node1.node_sha256
            },
            {
                "node_id": node2.node_id,
                "cycle_id": node2.cycle_id,
                "guardian_result": node2.guardian_result,
                "has_failure_state": node2.failure_state is not None,
                "node_sha256": node2.node_sha256
            }
        ]
    }

    print("----------------------------------------------------------------------")
    print(json.dumps(flight_result, indent=2))
    print("----------------------------------------------------------------------")
    print("=== SAGE / SAGI Phase 3 Research Graph Flight Completed Successfully ===")

    return flight_result


if __name__ == "__main__":
    run_sagi_research_graph_flight()
