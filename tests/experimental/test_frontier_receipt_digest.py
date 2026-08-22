from dataclasses import dataclass

from sage.experimental.frontier_receipt_digest import (
    frontier_receipt_digest,
    verify_frontier_receipt_digest,
)


@dataclass(frozen=True)
class Receipt:
    frontier_id: str
    observations: tuple[str, ...]


def test_digest_is_deterministic_and_ordered_by_mapping_keys():
    first = {"b": 2, "a": 1}
    second = {"a": 1, "b": 2}
    assert frontier_receipt_digest(first) == frontier_receipt_digest(second)


def test_dataclass_receipt_replays_exactly():
    receipt = Receipt("frontier", ("a", "b"))
    digest = frontier_receipt_digest(receipt)
    assert verify_frontier_receipt_digest(receipt, digest)


def test_tampered_receipt_or_digest_fails():
    receipt = Receipt("frontier", ("a", "b"))
    digest = frontier_receipt_digest(receipt)
    assert not verify_frontier_receipt_digest(Receipt("frontier", ("a", "c")), digest)
    assert not verify_frontier_receipt_digest(receipt, "bad")
