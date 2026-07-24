"""SAGE Persistent Append-Only Nonce Ledger for replay protection."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Set


class NonceLedger:
    """Manages an append-only persistent registry of used nonces to prevent replay attacks."""

    def __init__(self, storage_path: str | Path | None = None):
        """Initialize Nonce Ledger.

        Args:
            storage_path: Path to the JSON registry file.
        """
        self.storage_path = Path(storage_path or "sage_data/nonces.json")
        self.used_nonces: Set[str] = set()
        self._load_nonces()

    def _load_nonces(self) -> None:
        """Load registered nonces from the persistent ledger file."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and "nonce" in entry:
                            self.used_nonces.add(entry["nonce"])
        except (json.JSONDecodeError, OSError):
            # Fallback to reading lines as JSON elements
            try:
                with open(self.storage_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                if isinstance(entry, dict) and "nonce" in entry:
                                    self.used_nonces.add(entry["nonce"])
                            except Exception:
                                pass
            except Exception:
                pass

    def verify_and_record(self, nonce: str, context_info: str | None = None) -> bool:
        """Verify if a nonce is unique and record it to prevent future replays.

        Args:
            nonce: Unique nonce string.
            context_info: Optional string describing the context of the transaction.

        Returns:
            True if the nonce is unique and successfully recorded, False if already used (replay).
        """
        if not nonce:
            return True  # If no nonce is provided, we default to passing

        if nonce in self.used_nonces:
            return False  # Replay detected!

        # Unique nonce. Record it.
        self.used_nonces.add(nonce)
        self._append_nonce_to_file(nonce, context_info)
        return True

    def _append_nonce_to_file(self, nonce: str, context_info: str | None = None) -> None:
        """Append the new nonce to the persistent JSON ledger file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "nonce": nonce,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context_info or "unknown"
        }

        entries = []
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        entries = data
            except Exception:
                pass

        entries.append(entry)

        try:
            with open(self.storage_path, "w") as f:
                json.dump(entries, f, indent=2)
        except OSError:
            pass

    def clear(self) -> None:
        """Clear all registered nonces (primarily for testing)."""
        self.used_nonces.clear()
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
            except OSError:
                pass
