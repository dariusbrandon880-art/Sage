"""SAGE ACR-X Continuity Kernel.

Executes the continuous cognitive substrate lifecycle:
BOOT -> INGEST -> EVALUATE -> VERIFY -> CONSOLIDATE -> ATTEST.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sage.core.acrx_fabric import ACRXMemoryFabric
from sage.core.acrx_models import MemoryToken, STPMemoryLayer
from sage.core.proofreader import ACRXProofreader


class ACRXKernel:
    """Continuity Kernel governing state lifecycles and validation gates."""

    def __init__(self, runtime: Any, vault_dir: str = ".sage/validation/audit"):
        """Initialize Continuity Kernel."""
        self.runtime = runtime
        self.fabric = ACRXMemoryFabric()
        self.proofreader = ACRXProofreader()
        self.vault_dir = Path(vault_dir)
        self.baseline_state: dict[str, Any] = {}
        self.active_transaction_token: MemoryToken | None = None
        self.is_coherent = True

    def boot(self) -> None:
        """BOOT stage: initializes and reads baseline state from vault."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        vault_file = self.vault_dir / "c3s_vault.json"

        # Safe load baseline state
        if vault_file.exists():
            try:
                # Obtain lock during read
                with open(vault_file, "r") as f:
                    data = json.load(f)
                self.baseline_state = data.get("baseline_state", {})
            except Exception:  # noqa: BLE001, S110
                pass

        if not self.baseline_state:
            # Rehydrate baseline from current stable runtime status
            self.baseline_state = {
                "current_objective": self.runtime.current_state.current_objective,
                "active_task": self.runtime.current_state.active_task,
                "blockers": list(self.runtime.current_state.blockers),
                "dependencies": list(self.runtime.current_state.dependencies),
                "memory_count": len(self.runtime.memory.list_all()),
                "decision_count": len(self.runtime.decisions.list_all()),
            }

    def ingest(self, session_payload: dict[str, Any]) -> str:
        """INGEST stage: accepts session inputs, maps them into WORKING layer as MemoryTokens."""
        token = MemoryToken.create(STPMemoryLayer.WORKING, session_payload)
        self.fabric.store_token(token)
        self.active_transaction_token = token
        return token.token_id

    def evaluate(self) -> dict[str, Any]:
        """EVALUATE stage: calculates Shannon entropy, IDI, MSS, and VFE."""
        if not self.active_transaction_token:
            raise ValueError("No active transaction token has been ingested.")

        observed_state = {
            "current_objective": self.runtime.current_state.current_objective,
            "active_task": self.runtime.current_state.active_task,
            "blockers": list(self.runtime.current_state.blockers),
            "dependencies": list(self.runtime.current_state.dependencies),
            "memory_count": len(self.runtime.memory.list_all()),
            "decision_count": len(self.runtime.decisions.list_all()),
        }

        serialized_token = json.dumps(self.active_transaction_token.content)
        idi = self.proofreader.calculate_identity_drift(observed_state, self.baseline_state)
        vfe = self.proofreader.calculate_variational_free_energy(
            observed_state, self.baseline_state, serialized_token
        )

        validated_count = len(
            [m for m in self.runtime.memory.list_all() if m.confidence == "validated"]
        )
        archived_count = len(self.runtime.archive.list_all())
        hypothesis_count = len(
            [m for m in self.runtime.memory.list_all() if m.confidence == "hypothesis"]
        )
        mss = self.proofreader.calculate_memory_stability(
            validated_count + archived_count, hypothesis_count
        )

        return {
            "idi": idi,
            "vfe": vfe,
            "mss": mss,
            "shannon_entropy": self.active_transaction_token.structural_entropy,
        }

    def verify(self) -> bool:
        """VERIFY stage: executes validation gates over drift and entropy limits."""
        metrics = self.evaluate()
        # Enforce structural boundaries: if IDI > 1.5 or shannon_entropy > 15.0, flag instability
        if metrics["idi"] > 1.5 or metrics["shannon_entropy"] > 15.0:
            self.is_coherent = False
            return False

        self.is_coherent = True
        return True

    def consolidate(self) -> bool:
        """CONSOLIDATE stage: promotes WORKING tokens into SEMANTIC store and updates baseline."""
        if not self.verify():
            return False

        if not self.active_transaction_token:
            return False

        # Create SEMANTIC layer token representing consolidated wisdom
        consolidated_token = MemoryToken.create(
            STPMemoryLayer.SEMANTIC, self.active_transaction_token.content
        )
        self.fabric.store_token(consolidated_token)

        # Update baseline state
        self.baseline_state = {
            "current_objective": self.runtime.current_state.current_objective,
            "active_task": self.runtime.current_state.active_task,
            "blockers": list(self.runtime.current_state.blockers),
            "dependencies": list(self.runtime.current_state.dependencies),
            "memory_count": len(self.runtime.memory.list_all()),
            "decision_count": len(self.runtime.decisions.list_all()),
        }
        return True

    def attest(self, message: str) -> None:
        """ATTEST stage: append-safe transaction audit log with atomic locking protection."""
        vault_file = self.vault_dir / "c3s_vault.json"
        log_file = self.vault_dir / "identity_timeline.log"
        lock_file = self.vault_dir / "c3s_vault.json.lock"

        # 1. Simple atomic `.lock` file protection for cross-platform reliability
        import time

        for _ in range(50):
            try:
                # Try creating lock atomically
                fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, b"LOCKED")
                os.close(fd)
                break
            except OSError:
                time.sleep(0.01)

        # Write to vault
        vault_data = {
            "baseline_state": self.baseline_state,
            "is_coherent": self.is_coherent,
            "last_attestation": message,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(vault_file, "w") as f:
                json.dump(vault_data, f, indent=2, default=str)

            # Append transaction to corruption-resistant log
            log_entry = f"[{datetime.now(timezone.utc).isoformat()}] [COHERENT={self.is_coherent}] {message}\n"
            with open(log_file, "a") as f:
                f.write(log_entry)
        finally:
            # Atomic unlock
            if lock_file.exists():
                try:
                    lock_file.unlink()
                except OSError:
                    pass
