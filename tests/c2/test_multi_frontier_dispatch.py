from unittest.mock import MagicMock
from sage.c2.build_jump_wave import FlightMissionSpec, create_default_wave_missions
from sage.c2.multi_frontier_dispatch import MultiFrontierDispatcher, compute_receipt_hash


def test_multi_frontier_dispatch_executes_dynamic_missions():
    missions = create_default_wave_missions()
    dispatcher = MultiFrontierDispatcher(commit_sha="47bb765e03f1d07358ba783ce6ae69b1c8579167", missions=missions)
    receipt = dispatcher.dispatch_all()
    assert receipt.commit_sha == "47bb765e03f1d07358ba783ce6ae69b1c8579167"
    assert len(receipt.flight_receipts) == 5
    assert {r.flight_id for r in receipt.flight_receipts} == {m.flight_id for m in missions}
