import pytest

from sage.experimental.sagi_discovery_flight_selector import (
    DiscoveryCandidate,
    FlightRole,
    SAGIDiscoveryFlightSelector,
)
from sage.experimental.sagi_flight_wave import materialize_wave


def make_proposal():
    candidates = tuple(
        DiscoveryCandidate(
            str(i), f"candidate-{i}", role, 0.8, 0.8, 0.8, 1.0, 0.8, f"research-{i}"
        )
        for i, role in enumerate(FlightRole, 1)
    )
    return SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="frontier")


def test_five_selected_flights_materialize_to_twenty_cells():
    plan = materialize_wave(make_proposal())
    assert plan.expected_cell_count == 20
    assert len({cell.campaign_id for cell in plan.cells}) == 5
    assert len({cell.flight_cell for cell in plan.cells}) == 4


def test_each_campaign_contains_all_four_longitudinal_cells():
    plan = materialize_wave(make_proposal())
    for campaign in {cell.campaign_id for cell in plan.cells}:
        cells = {cell.flight_cell.value for cell in plan.cells if cell.campaign_id == campaign}
        assert cells == {"004", "005", "006", "007"}


def test_wave_requires_exactly_five_selected_flights():
    proposal = make_proposal()
    broken = proposal.__class__(proposal.candidates[:4], proposal.frontier_digest, proposal.selection_digest)
    with pytest.raises(ValueError, match="exactly five"):
        materialize_wave(broken)
