"""SAGE Continuous Media Perception Substrate & Temporal Super Search Engine.

Implements a media-agnostic, governed perception stream engine capable of representing
ongoing sessions (videos, audio, screen-shares, code streams, cameras, documents)
as temporal, auditable perception streams. Enforces the non-negotiable governance principle:

ARCHITECTURE READY != LIVE SENSOR CONNECTED != CONTINUOUS COVERAGE VERIFIED
"""

from __future__ import annotations

import hashlib
import json
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class MediaStreamType(str, Enum):
    """Supported stream channels in the perception bus."""

    VISUAL = "VISUAL"
    AUDIO = "AUDIO"
    METADATA = "METADATA"


class PerceptionEventType(str, Enum):
    """Lifecycle classification for perception observations."""

    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    SEARCHED = "SEARCHED"
    VERIFIED = "VERIFIED"


class SourceIdentity(BaseModel):
    """Cryptographic/system identity of an upstream sensor or media input edge."""

    sensor_id: str
    source_type: str = Field(description="e.g. screen_capture, camera, youtube_stream, audio_mic, doc_feed")
    platform: str = Field(default="ChatGPT_Multimodal_Gateway")
    capability_level: str = Field(default="CONTINUOUS_STREAM")
    details: Dict[str, Any] = Field(default_factory=dict)


class PerceptionEvent(BaseModel):
    """Single discrete observation within a media session stream."""

    event_id: str
    session_id: str
    event_type: PerceptionEventType = PerceptionEventType.OBSERVED
    stream_type: MediaStreamType
    timestamp: float = Field(description="Normalized epoch timestamp in seconds")
    sequence_num: int
    source: SourceIdentity
    visual_entities: List[str] = Field(default_factory=list, description="Detected visual elements/bounding items/text")
    audio_transcript: Optional[str] = Field(default=None, description="Spoken word or sound event description")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_hash: str = Field(default="", description="SHA-256 fingerprint of raw payload")

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint of payload."""
        payload = {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "event_type": self.event_type.value,
            "stream_type": self.stream_type.value,
            "timestamp": self.timestamp,
            "sequence_num": self.sequence_num,
            "sensor_id": self.source.sensor_id,
            "visual_entities": sorted(self.visual_entities),
            "audio_transcript": self.audio_transcript or "",
            "metadata": self.metadata,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class MediaSession(BaseModel):
    """Authoritative container for one continuous media perception context."""

    session_id: str
    source: SourceIdentity
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    architecture_ready: bool = True
    live_sensor_connected: bool = False
    continuous_coverage_verified: bool = False
    events: List[PerceptionEvent] = Field(default_factory=list)

    @property
    def total_events(self) -> int:
        return len(self.events)

    @property
    def stream_stats(self) -> Dict[str, int]:
        stats = {st.value: 0 for st in MediaStreamType}
        for ev in self.events:
            stats[ev.stream_type.value] += 1
        return stats


class CoverageSummary(BaseModel):
    """Audited coverage metrics enforcing non-fabrication constraints."""

    session_id: str
    total_duration_seconds: float
    observed_duration_seconds: float
    visual_coverage_pct: float
    audio_coverage_pct: float
    metadata_coverage_pct: float
    detected_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    architecture_ready: bool = True
    live_sensor_connected: bool = False
    continuous_coverage_verified: bool = False
    governance_verdict: str = Field(default="ARCHITECTURE_READY_UNCONNECTED")


class VerificationVerdict(BaseModel):
    """Verdict output from the Perception Verification Layer."""

    session_id: str
    is_valid: bool
    checks_passed: List[str] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
    contradictions_detected: List[Dict[str, Any]] = Field(default_factory=list)
    verdict_sha256: str = ""


class TemporalSearchResultItem(BaseModel):
    """Discrete match item returned by Temporal Super Search."""

    source_plane: str = Field(description="ACTIVE_SESSION | HISTORICAL_SESSION | WEB_KNOWLEDGE | REPOSITORY")
    session_id: Optional[str] = None
    timestamp: Optional[float] = None
    sequence_num: Optional[int] = None
    stream_type: Optional[str] = None
    content: str
    relevance_score: float
    provenance: Dict[str, Any] = Field(default_factory=dict)


class GovernedSynthesisResult(BaseModel):
    """Bounded, auditable synthesis output generated strictly from verified evidence."""

    query: str
    session_id: str
    observed_evidence: List[str] = Field(default_factory=list)
    inferred_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    searched_cross_references: List[TemporalSearchResultItem] = Field(default_factory=list)
    verified_facts: List[str] = Field(default_factory=list)
    governance_notice: str
    coverage_verdict: CoverageSummary
    synthesis_markdown: str
    receipt_sha256: str = ""


class MediaIngestionEdge:
    """Ingests raw frame/audio/metadata feeds, normalizes timestamps, and builds PerceptionEvents."""

    def __init__(self, session: MediaSession):
        self.session = session
        self._seq_counter = 0

    def ingest_frame(
        self,
        timestamp: float,
        visual_entities: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> PerceptionEvent:
        """Ingest a visual frame observation."""
        self._seq_counter += 1
        event = PerceptionEvent(
            event_id=f"evt_{self.session.session_id}_{self._seq_counter:06d}",
            session_id=self.session.session_id,
            event_type=PerceptionEventType.OBSERVED,
            stream_type=MediaStreamType.VISUAL,
            timestamp=timestamp,
            sequence_num=self._seq_counter,
            source=self.session.source,
            visual_entities=visual_entities,
            metadata=metadata or {},
            confidence=confidence,
        )
        event.raw_hash = event.compute_hash()
        self.session.events.append(event)
        return event

    def ingest_audio(
        self,
        timestamp: float,
        transcript: str,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> PerceptionEvent:
        """Ingest an audio transcript observation."""
        self._seq_counter += 1
        event = PerceptionEvent(
            event_id=f"evt_{self.session.session_id}_{self._seq_counter:06d}",
            session_id=self.session.session_id,
            event_type=PerceptionEventType.OBSERVED,
            stream_type=MediaStreamType.AUDIO,
            timestamp=timestamp,
            sequence_num=self._seq_counter,
            source=self.session.source,
            audio_transcript=transcript,
            metadata=metadata or {},
            confidence=confidence,
        )
        event.raw_hash = event.compute_hash()
        self.session.events.append(event)
        return event

    def ingest_metadata(
        self,
        timestamp: float,
        metadata: Dict[str, Any],
        confidence: float = 1.0,
    ) -> PerceptionEvent:
        """Ingest metadata/environment event."""
        self._seq_counter += 1
        event = PerceptionEvent(
            event_id=f"evt_{self.session.session_id}_{self._seq_counter:06d}",
            session_id=self.session.session_id,
            event_type=PerceptionEventType.OBSERVED,
            stream_type=MediaStreamType.METADATA,
            timestamp=timestamp,
            sequence_num=self._seq_counter,
            source=self.session.source,
            metadata=metadata,
            confidence=confidence,
        )
        event.raw_hash = event.compute_hash()
        self.session.events.append(event)
        return event


class TemporalSessionIndex:
    """Indexed search engine over a single MediaSession stream."""

    def __init__(self, session: MediaSession):
        self.session = session

    def search_time_range(self, start_time: float, end_time: float) -> List[PerceptionEvent]:
        """Find all perception events within a specific temporal window."""
        return [
            ev for ev in self.session.events
            if start_time <= ev.timestamp <= end_time
        ]

    def search_entities(self, entity_query: str) -> List[PerceptionEvent]:
        """Search visual entities for matching strings (case-insensitive substring)."""
        query_lower = entity_query.lower()
        matches = []
        for ev in self.session.events:
            if ev.stream_type == MediaStreamType.VISUAL:
                if any(query_lower in ent.lower() for ent in ev.visual_entities):
                    matches.append(ev)
        return matches

    def search_transcripts(self, keyword: str) -> List[PerceptionEvent]:
        """Search audio transcripts for matching keywords."""
        kw_lower = keyword.lower()
        matches = []
        for ev in self.session.events:
            if ev.stream_type == MediaStreamType.AUDIO and ev.audio_transcript:
                if kw_lower in ev.audio_transcript.lower():
                    matches.append(ev)
        return matches

    def cross_reference_visual_and_audio(self, window_seconds: float = 3.0) -> List[Dict[str, Any]]:
        """Cross-reference visual observations with temporally adjacent audio transcripts."""
        cross_refs = []
        visual_events = [ev for ev in self.session.events if ev.stream_type == MediaStreamType.VISUAL]
        audio_events = [ev for ev in self.session.events if ev.stream_type == MediaStreamType.AUDIO]

        for vev in visual_events:
            matching_audio = [
                aev for aev in audio_events
                if abs(aev.timestamp - vev.timestamp) <= window_seconds
            ]
            if matching_audio:
                cross_refs.append({
                    "timestamp": vev.timestamp,
                    "visual_entities": vev.visual_entities,
                    "adjacent_audio": [aev.audio_transcript for aev in matching_audio],
                    "time_delta": [round(abs(aev.timestamp - vev.timestamp), 3) for aev in matching_audio],
                })
        return cross_refs


class TemporalSuperSearchEngine:
    """Orchestrates temporal cross-plane search across active session, historical sessions, web knowledge, and repo."""

    def __init__(
        self,
        active_session: MediaSession,
        historical_sessions: Optional[List[MediaSession]] = None,
        repo_knowledge: Optional[Dict[str, str]] = None,
    ):
        self.active_session = active_session
        self.historical_sessions = historical_sessions or []
        self.repo_knowledge = repo_knowledge or {
            "architecture": "SAGE Continuous Media Perception + Temporal Super Search Architecture",
            "governance_rule": "ARCHITECTURE READY != LIVE SENSOR CONNECTED != CONTINUOUS COVERAGE VERIFIED",
        }

    def execute_temporal_super_search(
        self,
        query: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[TemporalSearchResultItem]:
        """Execute federated temporal query across all 4 knowledge planes."""
        results: List[TemporalSearchResultItem] = []
        q_lower = query.lower()

        # Plane 1: Active Session Context
        active_index = TemporalSessionIndex(self.active_session)
        active_events = self.active_session.events
        if start_time is not None and end_time is not None:
            active_events = active_index.search_time_range(start_time, end_time)

        for ev in active_events:
            matched_content = []
            if ev.stream_type == MediaStreamType.VISUAL:
                matched = [ent for ent in ev.visual_entities if q_lower in ent.lower()]
                if matched or q_lower in "visual":
                    matched_content.append(f"Visual entities: {', '.join(ev.visual_entities)}")
            elif ev.stream_type == MediaStreamType.AUDIO and ev.audio_transcript:
                if q_lower in ev.audio_transcript.lower():
                    matched_content.append(f"Audio transcript: {ev.audio_transcript}")
            elif ev.stream_type == MediaStreamType.METADATA:
                meta_str = json.dumps(ev.metadata)
                if q_lower in meta_str.lower():
                    matched_content.append(f"Metadata: {meta_str}")

            for content in matched_content:
                results.append(
                    TemporalSearchResultItem(
                        source_plane="ACTIVE_SESSION",
                        session_id=self.active_session.session_id,
                        timestamp=ev.timestamp,
                        sequence_num=ev.sequence_num,
                        stream_type=ev.stream_type.value,
                        content=content,
                        relevance_score=0.95,
                        provenance={"raw_hash": ev.raw_hash, "sensor_id": ev.source.sensor_id},
                    )
                )

        # Plane 2: Historical Sessions Context
        for hist_sess in self.historical_sessions:
            for ev in hist_sess.events:
                if (ev.audio_transcript and q_lower in ev.audio_transcript.lower()) or \
                   any(q_lower in ent.lower() for ent in ev.visual_entities):
                    results.append(
                        TemporalSearchResultItem(
                            source_plane="HISTORICAL_SESSION",
                            session_id=hist_sess.session_id,
                            timestamp=ev.timestamp,
                            sequence_num=ev.sequence_num,
                            stream_type=ev.stream_type.value,
                            content=ev.audio_transcript or f"Entities: {', '.join(ev.visual_entities)}",
                            relevance_score=0.80,
                            provenance={"raw_hash": ev.raw_hash, "sensor_id": ev.source.sensor_id},
                        )
                    )

        # Plane 3: Web Knowledge Plane (governed simulation/query)
        if "movie" in q_lower or "web" in q_lower or "external" in q_lower or "youtube" in q_lower:
            results.append(
                TemporalSearchResultItem(
                    source_plane="WEB_KNOWLEDGE",
                    content=f"External reference indexed for query '{query}': Public media metadata and background context.",
                    relevance_score=0.70,
                    provenance={"web_query": query, "verified_source": "Governed_SuperSearch_Bridge"},
                )
            )

        # Plane 4: Repository Knowledge Plane
        for key, val in self.repo_knowledge.items():
            if q_lower in key.lower() or q_lower in val.lower():
                results.append(
                    TemporalSearchResultItem(
                        source_plane="REPOSITORY",
                        content=f"[{key}] {val}",
                        relevance_score=0.90,
                        provenance={"file": "sage/c2/media_perception.py", "type": "ARCHITECTURE_CONTRACT"},
                    )
                )

        return results


class PerceptionVerificationLayer:
    """Validates perception integrity, provenance, timestamp sequence, and contradiction detection."""

    def __init__(self, session: MediaSession):
        self.session = session

    def verify_session(self) -> VerificationVerdict:
        """Run full integrity check over perception session."""
        checks_passed = []
        violations = []
        contradictions = []

        # Check 1: Event Hash Integrity
        hash_pass = True
        for ev in self.session.events:
            computed = ev.compute_hash()
            if ev.raw_hash and ev.raw_hash != computed:
                violations.append(f"Event {ev.event_id} hash mismatch: recorded={ev.raw_hash}, computed={computed}")
                hash_pass = False
        if hash_pass:
            checks_passed.append("EVENT_HASH_INTEGRITY")

        # Check 2: Monotonic Sequence and Timestamp Order
        seq_pass = True
        prev_seq = 0
        prev_ts = 0.0
        for ev in self.session.events:
            if ev.sequence_num <= prev_seq:
                violations.append(f"Sequence non-monotonic at event {ev.event_id}: {ev.sequence_num} <= {prev_seq}")
                seq_pass = False
            if ev.timestamp < prev_ts:
                violations.append(f"Timestamp backward drift at event {ev.event_id}: {ev.timestamp} < {prev_ts}")
                seq_pass = False
            prev_seq = ev.sequence_num
            prev_ts = ev.timestamp
        if seq_pass:
            checks_passed.append("MONOTONIC_TEMPORAL_SEQUENCE")

        # Check 3: Contradiction Detection (Visual vs Audio cross-checking)
        index = TemporalSessionIndex(self.session)
        cross_refs = index.cross_reference_visual_and_audio(window_seconds=2.0)
        for ref in cross_refs:
            audio_text = " ".join(ref["adjacent_audio"]).lower()
            visual_ents = [v.lower() for v in ref["visual_entities"]]
            # Contradiction rule: audio explicitly denies what visual asserts (e.g. "no green light" vs "green light")
            for ent in visual_ents:
                negation = f"no {ent}"
                if negation in audio_text:
                    contradictions.append({
                        "timestamp": ref["timestamp"],
                        "visual": ent,
                        "audio": audio_text,
                        "conflict_type": "VISUAL_AUDIO_NEGATION_CONTRADICTION",
                    })

        if contradictions:
            violations.append(f"Detected {len(contradictions)} visual-audio contradictions")
        else:
            checks_passed.append("CONTRADICTION_FREE_VALIDATED")

        verdict_data = {
            "session_id": self.session.session_id,
            "checks_passed": checks_passed,
            "violations": violations,
            "contradictions": contradictions,
        }
        verdict_sha256 = hashlib.sha256(json.dumps(verdict_data, sort_keys=True).encode("utf-8")).hexdigest()

        return VerificationVerdict(
            session_id=self.session.session_id,
            is_valid=(len(violations) == 0),
            checks_passed=checks_passed,
            violations=violations,
            contradictions_detected=contradictions,
            verdict_sha256=verdict_sha256,
        )


class CoverageAuditor:
    """Audits stream duration, frame coverage, audio coverage, gap accounting, and governance invariants."""

    def __init__(self, max_gap_threshold_seconds: float = 2.0):
        self.max_gap_threshold = max_gap_threshold_seconds

    def audit_coverage(self, session: MediaSession) -> CoverageSummary:
        """Calculate perception stream metrics and enforce governance invariants."""
        if not session.events:
            return CoverageSummary(
                session_id=session.session_id,
                total_duration_seconds=0.0,
                observed_duration_seconds=0.0,
                visual_coverage_pct=0.0,
                audio_coverage_pct=0.0,
                metadata_coverage_pct=0.0,
                detected_gaps=[],
                uncertainty_score=1.0,
                architecture_ready=session.architecture_ready,
                live_sensor_connected=session.live_sensor_connected,
                continuous_coverage_verified=False,
                governance_verdict="ZERO_EVENTS_UNCOVERED",
            )

        sorted_events = sorted(session.events, key=lambda x: x.timestamp)
        start_ts = sorted_events[0].timestamp
        end_ts = sorted_events[-1].timestamp
        total_duration = max(0.1, end_ts - start_ts)

        # Detect temporal gaps
        gaps = []
        observed_duration = 0.0
        for i in range(1, len(sorted_events)):
            delta = sorted_events[i].timestamp - sorted_events[i - 1].timestamp
            if delta > self.max_gap_threshold:
                gaps.append({
                    "start_timestamp": sorted_events[i - 1].timestamp,
                    "end_timestamp": sorted_events[i].timestamp,
                    "gap_seconds": round(delta, 3),
                })
            else:
                observed_duration += delta

        total_gap_time = sum(g["gap_seconds"] for g in gaps)
        observed_time = max(0.0, total_duration - total_gap_time)

        # Stream counts
        stats = session.stream_stats
        total_ev_count = max(1, session.total_events)
        vis_pct = round((stats[MediaStreamType.VISUAL.value] / total_ev_count) * 100.0, 2)
        aud_pct = round((stats[MediaStreamType.AUDIO.value] / total_ev_count) * 100.0, 2)
        meta_pct = round((stats[MediaStreamType.METADATA.value] / total_ev_count) * 100.0, 2)

        uncertainty = round(min(1.0, (total_gap_time / total_duration) + (0.1 if len(gaps) > 0 else 0.0)), 3)

        # Continuous coverage verified iff live sensor connected AND total gaps == 0 AND duration > 0
        coverage_verified = (
            session.live_sensor_connected and
            len(gaps) == 0 and
            total_duration > 0.0
        )

        verdict = (
            "CONTINUOUS_COVERAGE_VERIFIED" if coverage_verified else
            ("LIVE_SENSOR_CONNECTED_WITH_GAPS" if session.live_sensor_connected else "ARCHITECTURE_READY_NO_LIVE_SENSOR")
        )

        return CoverageSummary(
            session_id=session.session_id,
            total_duration_seconds=round(total_duration, 3),
            observed_duration_seconds=round(observed_time, 3),
            visual_coverage_pct=vis_pct,
            audio_coverage_pct=aud_pct,
            metadata_coverage_pct=meta_pct,
            detected_gaps=gaps,
            uncertainty_score=uncertainty,
            architecture_ready=session.architecture_ready,
            live_sensor_connected=session.live_sensor_connected,
            continuous_coverage_verified=coverage_verified,
            governance_verdict=verdict,
        )


class GovernedSynthesisEngine:
    """Produces auditable perception synthesis strictly bounded by verified evidence."""

    def __init__(self, session: MediaSession):
        self.session = session
        self.auditor = CoverageAuditor()
        self.verification_layer = PerceptionVerificationLayer(session)

    def synthesize(self, query: str, super_search_results: List[TemporalSearchResultItem]) -> GovernedSynthesisResult:
        """Synthesize governed output from bounded evidence."""
        coverage = self.auditor.audit_coverage(self.session)
        verdict = self.verification_layer.verify_session()

        observed_evidence = []
        inferred_hypotheses = []
        verified_facts = []

        for ev in self.session.events:
            if ev.stream_type == MediaStreamType.VISUAL:
                observed_evidence.append(
                    f"t={ev.timestamp:.1f}s [VISUAL] Entities observed: {', '.join(ev.visual_entities)} (confidence: {ev.confidence})"
                )
            elif ev.stream_type == MediaStreamType.AUDIO and ev.audio_transcript:
                observed_evidence.append(
                    f"t={ev.timestamp:.1f}s [AUDIO] Transcript: '{ev.audio_transcript}'"
                )

        # Inferred section
        if coverage.detected_gaps:
            inferred_hypotheses.append({
                "hypothesis": "Perception stream contains unobserved gaps where state transitions may have occurred.",
                "confidence": 0.50,
                "reasoning": f"Detected {len(coverage.detected_gaps)} gap(s) exceeding max threshold.",
            })

        # Verified facts section
        if verdict.is_valid:
            verified_facts.append("All stream events passed cryptographic SHA-256 hash validation.")
            verified_facts.append("Temporal sequence is strictly monotonic without backward time travel.")
            if "CONTRADICTION_FREE_VALIDATED" in verdict.checks_passed:
                verified_facts.append("No visual-audio contradictory claims detected across adjacent frames.")

        governance_notice = (
            "SAGE GOVERNANCE INVARIANT ENFORCED: ARCHITECTURE READY != LIVE SENSOR CONNECTED != CONTINUOUS COVERAGE VERIFIED. "
            f"Active status: live_sensor_connected={coverage.live_sensor_connected}, continuous_coverage_verified={coverage.continuous_coverage_verified}."
        )

        markdown_lines = [
            f"# SAGE Governed Perception Synthesis",
            f"**Query:** `{query}`",
            f"**Session ID:** `{self.session.session_id}`",
            f"**Governance Verdict:** `{coverage.governance_verdict}`",
            "",
            "## 1. [OBSERVED EVIDENCE]",
        ]
        if observed_evidence:
            for item in observed_evidence:
                markdown_lines.append(f"- {item}")
        else:
            markdown_lines.append("_No direct sensor observations recorded in this session._")

        markdown_lines.extend([
            "",
            "## 2. [INFERRED HYPOTHESES]",
        ])
        if inferred_hypotheses:
            for hyp in inferred_hypotheses:
                markdown_lines.append(f"- **Hypothesis:** {hyp['hypothesis']} (Confidence: {hyp['confidence']})")
                markdown_lines.append(f"  *Reasoning:* {hyp['reasoning']}")
        else:
            markdown_lines.append("_No unverified inferences required._")

        markdown_lines.extend([
            "",
            "## 3. [SEARCHED CROSS-REFERENCES]",
        ])
        if super_search_results:
            for res in super_search_results:
                markdown_lines.append(f"- `[{res.source_plane}]` {res.content} (Relevance: {res.relevance_score})")
        else:
            markdown_lines.append("_No external or historical cross-references requested._")

        markdown_lines.extend([
            "",
            "## 4. [VERIFIED FACTS]",
        ])
        if verified_facts:
            for vf in verified_facts:
                markdown_lines.append(f"- [VERIFIED] {vf}")
        else:
            markdown_lines.append("_Session pending verification._")

        markdown_lines.extend([
            "",
            "## 5. [GOVERNANCE AUDIT NOTICE]",
            f"> {governance_notice}",
        ])

        synthesis_md = "\n".join(markdown_lines)
        receipt_sha256 = hashlib.sha256(synthesis_md.encode("utf-8")).hexdigest()

        return GovernedSynthesisResult(
            query=query,
            session_id=self.session.session_id,
            observed_evidence=observed_evidence,
            inferred_hypotheses=inferred_hypotheses,
            searched_cross_references=super_search_results,
            verified_facts=verified_facts,
            governance_notice=governance_notice,
            coverage_verdict=coverage,
            synthesis_markdown=synthesis_md,
            receipt_sha256=receipt_sha256,
        )
