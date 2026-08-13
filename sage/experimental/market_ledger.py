"""SAGE Sports-Probability Scientific Research - Immutable Market Observation Ledger.

Implements the SAGE-RF-DATA-001 specification:
REAL MARKET OBSERVATION -> CANONICAL SNAPSHOT -> CRYPTOGRAPHIC INTEGRITY -> ORDERED RECORD -> REPLAY -> VERIFIED MARKET STATE.
"""

import hashlib
import json
import os
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field


class MarketObservation(BaseModel):
    """Immutable market observation record representing a single point-in-time sportsbook price."""
    schema_version: str = Field("SAGE-RF-DATA-001/v1.0", description="Schema and version identifier")
    market_identity: str = Field(..., description="Full unique market identity key (e.g. event:market:selection)")
    sportsbook: str = Field(..., description="Sportsbook name (e.g. FanDuel)")
    event_identity: str = Field(..., description="Unique event identity")
    market_type: str = Field(..., description="Market type (e.g. MONEYLINE, SPREAD)")
    selection: str = Field(..., description="Selection target")
    observed_price: float = Field(..., description="Observed price (decimal or American)")
    timestamp: str = Field(..., description="UTC ISO-8601 wall-clock timestamp of observation")
    sequence_id: int = Field(..., description="Deterministic process-local sequence identifier")
    payload_hash: str = Field("", description="SHA-256 canonical payload hash")

    def compute_canonical_hash(self) -> str:
        """Computes the deterministic SHA-256 hash of the canonical serialized payload."""
        # Exclude payload_hash itself from hashing
        payload_data = {
            "schema_version": self.schema_version,
            "market_identity": self.market_identity,
            "sportsbook": self.sportsbook,
            "event_identity": self.event_identity,
            "market_type": self.market_type,
            "selection": self.selection,
            "observed_price": self.observed_price,
            "timestamp": self.timestamp,
            "sequence_id": self.sequence_id
        }
        serialized = json.dumps(payload_data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class MarketLedger:
    """An append-only immutable ledger that registers, persists, and replays market observations."""

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path

    def read_records(self) -> List[MarketObservation]:
        """Loads and parses records from storage, verifying schema on load."""
        records = []
        if not os.path.exists(self.storage_path):
            return records

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        obs = MarketObservation(**data)
                        records.append(obs)
                    except Exception as e:
                        raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Malformed record on line {line_num}: {e}")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Error reading ledger storage: {e}")

        return records

    def ingest_observation(
        self,
        market_identity: str,
        sportsbook: str,
        event_identity: str,
        market_type: str,
        selection: str,
        observed_price: float,
        timestamp: str
    ) -> MarketObservation:
        """Ingests a new market observation, checking duplicates and appending to storage."""
        # Read existing records to compute the next monotonic sequence_id and check duplicates
        existing = self.read_records()
        next_seq = 1 if not existing else (existing[-1].sequence_id + 1)

        # Create temporary observation to compute canonical hash
        temp_obs = MarketObservation(
            market_identity=market_identity,
            sportsbook=sportsbook,
            event_identity=event_identity,
            market_type=market_type,
            selection=selection,
            observed_price=observed_price,
            timestamp=timestamp,
            sequence_id=next_seq
        )
        computed_hash = temp_obs.compute_canonical_hash()
        temp_obs.payload_hash = computed_hash

        # EXACT DUPLICATE POLICY:
        # Repeated observation of an unchanged market state (same market, sportsbook, event, price, selection)
        # must be detected. If an exact duplicate with the same payload_hash exists in the existing records,
        # we suppress it to avoid log pollution (or rather, return the existing one without appending).
        for obs in existing:
            if obs.market_identity == temp_obs.market_identity and \
               obs.sportsbook == temp_obs.sportsbook and \
               obs.event_identity == temp_obs.event_identity and \
               obs.market_type == temp_obs.market_type and \
               obs.selection == temp_obs.selection and \
               abs(obs.observed_price - temp_obs.observed_price) < 1e-9 and \
               obs.timestamp == temp_obs.timestamp:
                return obs

        # Write to append-only file
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.storage_path)), exist_ok=True)
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(temp_obs.model_dump_json() + "\n")
        except Exception as e:
            raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Failed to append record to ledger: {e}")

        return temp_obs

    def replay_ledger(self) -> Dict[str, float]:
        """Replays all stored observations sequentially and reconstructs the latest verified market state map.

        Replay Invariants Checked:
        1. Record Schema consistency.
        2. Canonical Serialization matches payload_hash.
        3. Observation Hash is untampered.
        4. Monotonic Sequence Ordering matches chronological sequence id.
        5. Market Identity integrity is isolated.
        6. Chronological reconstruction.
        7. Deterministic resulting state.

        Returns:
            Dict[str, float]: Reconstructed valid market state mapping full market identity key -> latest observed price.
        """
        records = self.read_records()
        state_map: Dict[str, float] = {}
        expected_seq = 1

        for i, obs in enumerate(records):
            # Invariant 1: Record Schema consistency
            if obs.schema_version != "SAGE-RF-DATA-001/v1.0":
                raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Inconsistent schema version '{obs.schema_version}' in sequence {obs.sequence_id}")

            # Invariant 2 & 3: Canonical serialization and payload hash matching (detect tampering)
            recomputed = obs.compute_canonical_hash()
            if obs.payload_hash != recomputed:
                raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Cryptographic integrity failure for sequence {obs.sequence_id}. Hash mismatch.")

            # Invariant 4: Monotonic sequence ordering (no gaps or out-of-order)
            if obs.sequence_id != expected_seq:
                raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Monotonic sequence break at sequence {obs.sequence_id} (expected {expected_seq})")

            # Invariant 5: Market Identity isolation is validated (market_identity must contain selection detail to prevent collapse)
            if ":" not in obs.market_identity:
                raise RuntimeError(f"STALE/CONFLICTED PROJECTION: Invalid non-isolated market identity '{obs.market_identity}' in sequence {obs.sequence_id}")

            # Invariant 6: Chronological reconstruction
            # Monotonic sequence id establishes the definitive chronology in this domain.

            # Invariant 7: Reconstruct state map
            state_map[obs.market_identity] = obs.observed_price
            expected_seq += 1

        return state_map
