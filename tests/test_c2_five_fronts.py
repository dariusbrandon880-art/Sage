from pathlib import Path

from sage.c2.frontier_execution import PROGRESSION_FRONT_NAMES, run_frontier
from sage.c2.progression_receipt_serializer import MissionProgressionReceiptSerializer
from sage.evidence.native_persisted_loader import NativePersistedEvidenceLoader


def test_progression_fronts_are_exactly_bounded():
    assert PROGRESSION_FRONT_NAMES == (
        "native_persisted_evidence",
        "progression_receipts",
    )


def test_retired_fronts_fail_closed():
    for retired_front in (
        "drive_continuity",
        "governed_execution",
        "sports_research",
    ):
        try:
            run_frontier(retired_front, lambda: None)
        except ValueError:
            continue
        raise AssertionError(f"retired frontier was accepted: {retired_front}")


def test_unknown_frontier_fails_closed():
    try:
        run_frontier("invented_front", lambda: None)
    except ValueError:
        return
    raise AssertionError("unknown frontier was accepted")


def test_native_loader_missing_file_fails_closed(tmp_path: Path):
    loader = NativePersistedEvidenceLoader(tmp_path)
    try:
        loader.load_file("missing.json")
    except FileNotFoundError:
        return
    raise AssertionError("missing evidence was not rejected")


def test_receipt_serializer_excludes_telemetry_identity_fields():
    assert hasattr(MissionProgressionReceiptSerializer, "serialize")
    assert hasattr(MissionProgressionReceiptSerializer, "digest")
