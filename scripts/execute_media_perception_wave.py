#!/usr/bin/env python3
"""Runner script for Continuous Media Perception & Temporal Super Search Wave.

Executes 5 flights traversing all milestone gates, producing a SHA-256 bound evidence package
persisted at evidence_capture/media_perception_wave_evidence.json.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from sage.c2.media_perception import (
    CoverageAuditor,
    GovernedSynthesisEngine,
    MediaIngestionEdge,
    MediaSession,
    MediaStreamType,
    PerceptionVerificationLayer,
    SourceIdentity,
    TemporalSessionIndex,
    TemporalSuperSearchEngine,
)


def get_git_head_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_HEAD_SHA"


def main() -> int:
    print("=========================================================================")
    print("Executing SAGE Continuous Media Perception & Temporal Super Search Wave")
    print("=========================================================================")

    head_sha = get_git_head_sha()
    print(f"Bound Git HEAD SHA: {head_sha}")

    source = SourceIdentity(
        sensor_id="sensor_chatgpt_multimodal_edge_01",
        source_type="screen_and_audio_feed",
        platform="ChatGPT_Multimodal_Gateway",
        capability_level="CONTINUOUS_STREAM",
    )

    flight_receipts = []

    # -------------------------------------------------------------------------
    # Flight 1: Ingestion Edge & Session Substrate
    # -------------------------------------------------------------------------
    print("\n--- Flight 1: Ingestion Edge & Session Substrate ---")
    session_f1 = MediaSession(session_id="wave_session_01", source=source, architecture_ready=True, live_sensor_connected=True)
    edge_f1 = MediaIngestionEdge(session_f1)

    ev1 = edge_f1.ingest_frame(timestamp=100.0, visual_entities=["SAGE Observatory Dashboard", "Telemetry Graph"])
    ev2 = edge_f1.ingest_audio(timestamp=101.0, transcript="Observing system health and active flights.")
    ev3 = edge_f1.ingest_metadata(timestamp=101.5, metadata={"active_view": "Observatory_HUD"})

    f1_passed = (session_f1.total_events == 3) and (ev1.raw_hash != "")
    flight_receipts.append({
        "flight_id": "FLIGHT-MEDIA-INGEST-EDGE",
        "passed": f1_passed,
        "events_ingested": session_f1.total_events,
        "stream_stats": session_f1.stream_stats,
    })
    print(f"Flight 1 Status: {'PASS' if f1_passed else 'FAIL'}")

    # -------------------------------------------------------------------------
    # Flight 2: Temporal Session Indexing & Cross-Referencing
    # -------------------------------------------------------------------------
    print("\n--- Flight 2: Temporal Session Indexing & Cross-Referencing ---")
    index_f2 = TemporalSessionIndex(session_f1)
    range_evs = index_f2.search_time_range(99.0, 102.0)
    ent_evs = index_f2.search_entities("Observatory")
    tr_evs = index_f2.search_transcripts("health")
    xrefs = index_f2.cross_reference_visual_and_audio(window_seconds=2.0)

    f2_passed = (len(range_evs) == 3) and (len(ent_evs) >= 1) and (len(tr_evs) >= 1) and (len(xrefs) >= 1)
    flight_receipts.append({
        "flight_id": "FLIGHT-TEMPORAL-SESSION-INDEX",
        "passed": f2_passed,
        "range_matches": len(range_evs),
        "entity_matches": len(ent_evs),
        "transcript_matches": len(tr_evs),
        "cross_references": len(xrefs),
    })
    print(f"Flight 2 Status: {'PASS' if f2_passed else 'FAIL'}")

    # -------------------------------------------------------------------------
    # Flight 3: Temporal Super Search Engine Across 4 Planes
    # -------------------------------------------------------------------------
    print("\n--- Flight 3: Temporal Super Search Engine Across 4 Planes ---")
    hist_session = MediaSession(session_id="hist_wave_session_01", source=source)
    hist_edge = MediaIngestionEdge(hist_session)
    hist_edge.ingest_audio(timestamp=10.0, transcript="Historical Observatory flight log recording.")

    repo_knowledge = {
        "observatory_architecture": "SAGE Observatory HUD & Continuous Perception Surface Integration",
        "governance_rule": "ARCHITECTURE READY != LIVE SENSOR CONNECTED != CONTINUOUS COVERAGE VERIFIED",
    }

    search_engine = TemporalSuperSearchEngine(
        active_session=session_f1,
        historical_sessions=[hist_session],
        repo_knowledge=repo_knowledge,
    )
    search_results = search_engine.execute_temporal_super_search(query="Observatory")
    planes_found = {r.source_plane for r in search_results}

    f3_passed = len(search_results) >= 2 and ("ACTIVE_SESSION" in planes_found) and ("REPOSITORY" in planes_found)
    flight_receipts.append({
        "flight_id": "FLIGHT-TEMPORAL-SUPER-SEARCH",
        "passed": f3_passed,
        "total_results": len(search_results),
        "planes_represented": sorted(list(planes_found)),
    })
    print(f"Flight 3 Status: {'PASS' if f3_passed else 'FAIL'}")

    # -------------------------------------------------------------------------
    # Flight 4: Perception Verification Layer & Coverage Auditor
    # -------------------------------------------------------------------------
    print("\n--- Flight 4: Perception Verification Layer & Coverage Auditor ---")
    verifier = PerceptionVerificationLayer(session_f1)
    verdict = verifier.verify_session()

    auditor = CoverageAuditor(max_gap_threshold_seconds=2.0)
    coverage = auditor.audit_coverage(session_f1)

    f4_passed = verdict.is_valid and coverage.continuous_coverage_verified
    flight_receipts.append({
        "flight_id": "FLIGHT-VERIFICATION-AND-COVERAGE-AUDIT",
        "passed": f4_passed,
        "verification_passed": verdict.is_valid,
        "coverage_verdict": coverage.governance_verdict,
        "continuous_coverage_verified": coverage.continuous_coverage_verified,
        "uncertainty_score": coverage.uncertainty_score,
    })
    print(f"Flight 4 Status: {'PASS' if f4_passed else 'FAIL'}")

    # -------------------------------------------------------------------------
    # Flight 5: Governed Perception Synthesis & Evidence Receipt
    # -------------------------------------------------------------------------
    print("\n--- Flight 5: Governed Perception Synthesis & Evidence Receipt ---")
    synthesis_engine = GovernedSynthesisEngine(session_f1)
    synthesis = synthesis_engine.synthesize(
        query="Synthesize current Observatory state and media perception telemetry",
        super_search_results=search_results,
    )

    f5_passed = (synthesis.receipt_sha256 != "") and ("OBSERVED EVIDENCE" in synthesis.synthesis_markdown)
    flight_receipts.append({
        "flight_id": "FLIGHT-GOVERNED-PERCEPTION-SYNTHESIS",
        "passed": f5_passed,
        "receipt_sha256": synthesis.receipt_sha256,
        "synthesis_markdown_length": len(synthesis.synthesis_markdown),
    })
    print(f"Flight 5 Status: {'PASS' if f5_passed else 'FAIL'}")

    # Overall Wave Reconvergence
    wave_passed = all(fr["passed"] for fr in flight_receipts)

    evidence_package = {
        "wave_id": "MEDIA_PERCEPTION_TEMPORAL_SUPER_SEARCH_WAVE_001",
        "head_sha": head_sha,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave_verdict": "PASS" if wave_passed else "FAIL",
        "governance_invariant": "ARCHITECTURE READY != LIVE SENSOR CONNECTED != CONTINUOUS COVERAGE VERIFIED",
        "flights": flight_receipts,
        "synthesis_sample": {
            "query": synthesis.query,
            "governance_notice": synthesis.governance_notice,
            "receipt_sha256": synthesis.receipt_sha256,
        },
    }

    serialized_evidence = json.dumps(evidence_package, sort_keys=True, indent=2)
    evidence_sha256 = hashlib.sha256(serialized_evidence.encode("utf-8")).hexdigest()
    evidence_package["evidence_digest"] = evidence_sha256

    output_dir = Path("evidence_capture")
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "media_perception_wave_evidence.json"

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_package, f, indent=2)

    print("\n=========================================================================")
    print(f"Wave Verdict: {'PASS' if wave_passed else 'FAIL'}")
    print(f"Evidence Persisted: {evidence_path}")
    print(f"Evidence SHA-256: {evidence_sha256}")
    print("=========================================================================")

    return 0 if wave_passed else 1


if __name__ == "__main__":
    sys.exit(main())
