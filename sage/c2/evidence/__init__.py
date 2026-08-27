"""Canonical SAGE execution-evidence primitives.

The evidence package is intentionally separate from legacy flat-file wave logs.
Gate authority belongs to SHA/run/job/digest-bound receipts validated by the
Local Integrity Kernel (LIK) and reconvergence aggregator.
"""

from .receipt_schema import ProvenanceTuple, StrictEvidenceReceipt
from .aggregator import AggregatorError, FrontState, ReconvergenceAggregator
from .registry import ImmutableEvidenceRegistry

__all__ = [
    "AggregatorError",
    "FrontState",
    "ImmutableEvidenceRegistry",
    "ProvenanceTuple",
    "ReconvergenceAggregator",
    "StrictEvidenceReceipt",
]
