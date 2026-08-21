"""Adversarial tests for verified agent progression."""

import pytest

from sage.experimental.agent_progression import (
    AgentProgression,
    AgentRank,
    ProgressionEventKind,
    VerifiedProgressionEvent,
    apply_verified_events,
    build_flight_status,
)


def event(event_id, kind, xp, capability=None):
    return VerifiedProgressionEvent(
        event_id=event_id,
        agent_id="agent_c2",
        mission_id="mission-1",
        kind=kind,
        xp_delta=xp,
        verification_reference=f"receipt:{event_id}",
        capability=capability,
    )


def test_agents_start_at_cql_zero_and_rank_comes_from_verified_xp():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control/C2")
    assert agent.rank == AgentRank.CQL_0
    assert agent.xp == 0

    apply_verified_events(
        agent,
        [event("e1", ProgressionEventKind.MISSION_SUCCESS, 100)],
    )
    assert agent.rank == AgentRank.CQL_1


def test_unverified_progression_event_is_rejected():
    with pytest.raises(ValueError, match="independent verification"):
        VerifiedProgressionEvent(
            event_id="e1",
            agent_id="agent_c2",
            mission_id="mission-1",
            kind=ProgressionEventKind.MISSION_SUCCESS,
            xp_delta=100,
            verification_reference="",
        )


def test_governance_violation_cannot_award_xp():
    with pytest.raises(ValueError, match="cannot award XP"):
        event("bad", ProgressionEventKind.GOVERNANCE_VIOLATION, 10)


def test_failure_recovery_can_compound_without_erasing_failure_history():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control/C2")
    apply_verified_events(
        agent,
        [
            event("failure", ProgressionEventKind.GOVERNANCE_VIOLATION, -25),
            event("recovery", ProgressionEventKind.FAILURE_RECOVERY, 75),
        ],
    )
    assert agent.xp == 50
    assert agent.governance_violations == 1
    assert agent.mission_count == 1


def test_qualification_requires_verified_capability_evidence():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control/C2")
    assert not agent.qualification("repo-recon")

    apply_verified_events(
        agent,
        [event("cap", ProgressionEventKind.VERIFIED_CAPABILITY, 25, "repo-recon")],
    )
    assert agent.qualification("repo-recon")
    assert not agent.qualification("autonomous-merge")


def test_duplicate_event_fails_closed():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control/C2")
    first = event("e1", ProgressionEventKind.MISSION_SUCCESS, 100)
    agent.apply(first)
    with pytest.raises(ValueError, match="Duplicate progression event"):
        agent.apply(first)


def test_canonical_digest_is_stable_for_same_state():
    def make_agent():
        agent = AgentProgression(agent_id="agent_c2", station="Mission Control/C2")
        agent.apply(event("e1", ProgressionEventKind.MISSION_SUCCESS, 100))
        return agent

    assert make_agent().canonical_digest() == make_agent().canonical_digest()


def test_flight_status_is_truthful_and_immersive():
    agent = AgentProgression(agent_id="agent_c2", station="Mission Control/C2")
    agent.apply(event("cap", ProgressionEventKind.VERIFIED_CAPABILITY, 100, "repo-recon"))
    status = build_flight_status(
        theater="Lane 2 — Governed Execution",
        mission_id="DOGFOOD-001",
        frontier="Verified agent progression",
        threat="pretend progress",
        victory_condition="verified progression event",
        agent=agent,
    )
    assert "THEATER: Lane 2 — Governed Execution" in status
    assert "RANK: CQL-1  XP: 100" in status
    assert "QUALIFIED: repo-recon" in status
    assert "VICTORY CONDITION: verified progression event" in status
