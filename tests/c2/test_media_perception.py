"""Tests for Continuous Media Perception & Temporal Super Search Engine."""

import time
import pytest
from sage.c2.media_perception import (
    CoverageAuditor,
    GovernedSynthesisEngine,
    MediaIngestionEdge,
    MediaSession,
    MediaStreamType,
    PerceptionEventType,
    PerceptionVerificationLayer,
    SourceIdentity,
    TemporalSessionIndex,
    TemporalSuperSearchEngine,
)


@pytest.fixture
def sample_source() -> SourceIdentity:
    return SourceIdentity(
        sensor_id="sensor_chatgpt_vision_01",
        source_type="screen_capture",
        platform="ChatGPT_Multimodal_Gateway",
        capability_level="CONTINUOUS_STREAM",
    )


def test_media_session_and_ingestion(sample_source: SourceIdentity):
    session = MediaSession(
        session_id="session_test_100",
        source=sample_source,
        start_time=1000.0,
        architecture_ready=True,
        live_sensor_connected=True,
    )
    edge = MediaIngestionEdge(session)

    evt1 = edge.ingest_frame(
        timestamp=1000.5,
        visual_entities=["code_editor", "python_file"],
        metadata={"resolution": "1920x1080"},
    )
    evt2 = edge.ingest_audio(
        timestamp=1001.0,
        transcript="Looking at the continuous media perception module.",
    )
    evt3 = edge.ingest_metadata(
        timestamp=1001.5,
        metadata={"active_window": "VSCode"},
    )

    assert session.total_events == 3
    assert evt1.sequence_num == 1
    assert evt2.sequence_num == 2
    assert evt3.sequence_num == 3

    assert evt1.raw_hash != ""
    assert evt1.compute_hash() == evt1.raw_hash

    stats = session.stream_stats
    assert stats[MediaStreamType.VISUAL.value] == 1
    assert stats[MediaStreamType.AUDIO.value] == 1
    assert stats[MediaStreamType.METADATA.value] == 1


def test_temporal_session_index(sample_source: SourceIdentity):
    session = MediaSession(session_id="session_test_200", source=sample_source)
    edge = MediaIngestionEdge(session)

    edge.ingest_frame(timestamp=10.0, visual_entities=["red light", "traffic_signal"])
    edge.ingest_audio(timestamp=11.0, transcript="Vehicle stopping at red light")
    edge.ingest_frame(timestamp=15.0, visual_entities=["green light", "moving_car"])
    edge.ingest_audio(timestamp=15.2, transcript="Vehicle accelerating on green light")

    index = TemporalSessionIndex(session)

    # Time range query
    range_events = index.search_time_range(9.0, 12.0)
    assert len(range_events) == 2

    # Entity search
    green_events = index.search_entities("green light")
    assert len(green_events) == 1
    assert "green light" in green_events[0].visual_entities

    # Transcript search
    stopping_events = index.search_transcripts("stopping")
    assert len(stopping_events) == 1
    assert "stopping" in stopping_events[0].audio_transcript

    # Cross reference
    xrefs = index.cross_reference_visual_and_audio(window_seconds=1.0)
    assert len(xrefs) == 2
    assert xrefs[0]["visual_entities"] == ["red light", "traffic_signal"]
    assert "Vehicle stopping at red light" in xrefs[0]["adjacent_audio"]


def test_temporal_super_search_engine(sample_source: SourceIdentity):
    active_session = MediaSession(session_id="active_sess_01", source=sample_source)
    edge_active = MediaIngestionEdge(active_session)
    edge_active.ingest_frame(timestamp=100.0, visual_entities=["dashboard", "chart_plot"])
    edge_active.ingest_audio(timestamp=101.0, transcript="Analyzing chart plot performance")

    hist_session = MediaSession(session_id="hist_sess_01", source=sample_source)
    edge_hist = MediaIngestionEdge(hist_session)
    edge_hist.ingest_audio(timestamp=50.0, transcript="Previous benchmark run for chart plot")

    search_engine = TemporalSuperSearchEngine(
        active_session=active_session,
        historical_sessions=[hist_session],
    )

    results = search_engine.execute_temporal_super_search(query="chart plot")
    planes = {r.source_plane for r in results}

    assert "ACTIVE_SESSION" in planes
    assert "HISTORICAL_SESSION" in planes
    assert len(results) >= 2


def test_perception_verification_layer_and_contradiction(sample_source: SourceIdentity):
    session = MediaSession(session_id="verify_sess_01", source=sample_source)
    edge = MediaIngestionEdge(session)

    # Contradictory inputs: Visual says "green light", Audio says "no green light"
    edge.ingest_frame(timestamp=10.0, visual_entities=["green light"])
    edge.ingest_audio(timestamp=10.5, transcript="There is no green light visible")

    verifier = PerceptionVerificationLayer(session)
    verdict = verifier.verify_session()

    assert not verdict.is_valid
    assert len(verdict.contradictions_detected) == 1
    assert verdict.contradictions_detected[0]["visual"] == "green light"
    assert "VISUAL_AUDIO_NEGATION_CONTRADICTION" in verdict.contradictions_detected[0]["conflict_type"]


def test_coverage_auditor_and_governance_invariants(sample_source: SourceIdentity):
    # Case A: Architecture Ready, but Live Sensor NOT connected
    session_unconnected = MediaSession(
        session_id="unconnected_sess",
        source=sample_source,
        architecture_ready=True,
        live_sensor_connected=False,
    )
    edge_u = MediaIngestionEdge(session_unconnected)
    edge_u.ingest_frame(timestamp=1.0, visual_entities=["frame1"])
    edge_u.ingest_frame(timestamp=2.0, visual_entities=["frame2"])

    auditor = CoverageAuditor(max_gap_threshold_seconds=2.0)
    summary_u = auditor.audit_coverage(session_unconnected)

    assert summary_u.architecture_ready is True
    assert summary_u.live_sensor_connected is False
    assert summary_u.continuous_coverage_verified is False
    assert summary_u.governance_verdict == "ARCHITECTURE_READY_NO_LIVE_SENSOR"

    # Case B: Live Sensor connected WITH gaps
    session_gaps = MediaSession(
        session_id="gaps_sess",
        source=sample_source,
        architecture_ready=True,
        live_sensor_connected=True,
    )
    edge_g = MediaIngestionEdge(session_gaps)
    edge_g.ingest_frame(timestamp=1.0, visual_entities=["frame1"])
    edge_g.ingest_frame(timestamp=10.0, visual_entities=["frame2"])  # 9s gap > 2s

    summary_g = auditor.audit_coverage(session_gaps)
    assert summary_g.live_sensor_connected is True
    assert len(summary_g.detected_gaps) == 1
    assert summary_g.detected_gaps[0]["gap_seconds"] == 9.0
    assert summary_g.continuous_coverage_verified is False
    assert summary_g.governance_verdict == "LIVE_SENSOR_CONNECTED_WITH_GAPS"

    # Case C: Live Sensor connected WITHOUT gaps -> Continuous Coverage Verified
    session_continuous = MediaSession(
        session_id="continuous_sess",
        source=sample_source,
        architecture_ready=True,
        live_sensor_connected=True,
    )
    edge_c = MediaIngestionEdge(session_continuous)
    edge_c.ingest_frame(timestamp=1.0, visual_entities=["frame1"])
    edge_c.ingest_frame(timestamp=2.0, visual_entities=["frame2"])
    edge_c.ingest_audio(timestamp=2.5, transcript="continuous stream active")

    summary_c = auditor.audit_coverage(session_continuous)
    assert summary_c.live_sensor_connected is True
    assert len(summary_c.detected_gaps) == 0
    assert summary_c.continuous_coverage_verified is True
    assert summary_c.governance_verdict == "CONTINUOUS_COVERAGE_VERIFIED"


def test_governed_synthesis_engine(sample_source: SourceIdentity):
    session = MediaSession(
        session_id="synth_sess_01",
        source=sample_source,
        architecture_ready=True,
        live_sensor_connected=True,
    )
    edge = MediaIngestionEdge(session)
    edge.ingest_frame(timestamp=100.0, visual_entities=["terminal", "pytest output"])
    edge.ingest_audio(timestamp=100.5, transcript="Executing unit test suite")

    search_engine = TemporalSuperSearchEngine(active_session=session)
    search_results = search_engine.execute_temporal_super_search(query="pytest")

    synthesis_engine = GovernedSynthesisEngine(session)
    res = synthesis_engine.synthesize(query="What is SAGE doing?", super_search_results=search_results)

    assert res.query == "What is SAGE doing?"
    assert res.session_id == "synth_sess_01"
    assert len(res.observed_evidence) == 2
    assert len(res.searched_cross_references) >= 1
    assert res.receipt_sha256 != ""
    assert "SAGE GOVERNANCE INVARIANT ENFORCED" in res.governance_notice
    assert "## 1. [OBSERVED EVIDENCE]" in res.synthesis_markdown
    assert "## 2. [INFERRED HYPOTHESES]" in res.synthesis_markdown
    assert "## 3. [SEARCHED CROSS-REFERENCES]" in res.synthesis_markdown
    assert "## 4. [VERIFIED FACTS]" in res.synthesis_markdown
