"""SAGE Experimental State Backup and Rehydration Manager.

Implements Milestone 1.1: Stateless Backup Persistence under experimental isolation.
Enables serialization, checksum verification, and graceful recovery of state snapshots.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class StateBackupManager:
    """Manages serialization, checksum validation, and recovery of experimental states.

    Designed to resolve stateless data loss risks on container restarts.
    """

    def __init__(self, backup_dir: str = "sage_data/experimental_backups"):
        """Initialize the backup manager with a designated storage directory."""
        self.backup_dir = backup_dir

    def _ensure_dir(self) -> None:
        """Create the backup directory if it does not already exist."""
        os.makedirs(self.backup_dir, exist_ok=True)

    def _compute_checksum(self, data_str: str) -> str:
        """Compute the SHA-256 checksum of a serialized state payload string."""
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    def backup_state(self, state_dict: Dict[str, Any], backup_id: str) -> str:
        """Serializes and saves the active state dictionary along with an integrity header.

        Args:
            state_dict: The dictionary payload representing the active SAGE state.
            backup_id: Unique identifier for the backup snapshot.

        Returns:
            The absolute or relative file path to the saved backup JSON.

        Raises:
            ValueError: If inputs are invalid or empty.
        """
        if not backup_id or not isinstance(backup_id, str) or not backup_id.strip():
            raise ValueError("Backup Violation: backup_id must be a non-empty string.")

        if not isinstance(state_dict, dict):
            raise ValueError("Backup Violation: state_dict must be a dictionary.")

        self._ensure_dir()

        # Serialize state dict to a canonical JSON string (sorted keys, no spaces)
        canonical_state = json.dumps(state_dict, sort_keys=True)
        checksum = self._compute_checksum(canonical_state)

        # Build envelope with metadata and integrity headers
        envelope = {
            "backup_id": backup_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "checksum": checksum,
            "payload": state_dict,
        }

        backup_filename = f"{backup_id}.json"
        filepath = os.path.join(self.backup_dir, backup_filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, sort_keys=True)

        return filepath

    def restore_state(self, backup_id: str) -> Dict[str, Any]:
        """Loads a backup snapshot, validates its SHA-256 integrity, and rehydrates state.

        Args:
            backup_id: Unique identifier for the backup snapshot to restore.

        Returns:
            The raw state payload dictionary inside the backup snapshot.

        Raises:
            FileNotFoundError: If the specified backup file does not exist.
            ValueError: If the file is malformed or has been modified/corrupted.
        """
        if not backup_id or not isinstance(backup_id, str) or not backup_id.strip():
            raise ValueError("Backup Violation: backup_id must be a non-empty string.")

        backup_filename = f"{backup_id}.json"
        filepath = os.path.join(self.backup_dir, backup_filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Backup Error: Snapshot '{backup_id}' not found at '{filepath}'.")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                envelope = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Backup Error: Malformed JSON structure inside backup file '{filepath}': {e}")

        # Check required envelope fields
        required_fields = ["backup_id", "created_at", "checksum", "payload"]
        for field in required_fields:
            if field not in envelope:
                raise ValueError(f"Backup Error: Missing required envelope field '{field}' in snapshot '{backup_id}'.")

        payload = envelope["payload"]
        if not isinstance(payload, dict):
            raise ValueError("Backup Error: Invalid payload type. Payload must be a dictionary.")

        # Re-compute and compare checksum to verify integrity
        canonical_payload = json.dumps(payload, sort_keys=True)
        expected_checksum = self._compute_checksum(canonical_payload)

        if envelope["checksum"] != expected_checksum:
            raise ValueError(
                f"Backup Error: SHA-256 checksum mismatch detected in snapshot '{backup_id}'! "
                f"Stored: {envelope['checksum']}, Computed: {expected_checksum}. State is corrupted or tampered."
            )

        return payload

    def list_backups(self) -> List[str]:
        """Returns a list of all available backup identifiers inside the backup directory."""
        if not os.path.exists(self.backup_dir):
            return []

        backups = []
        for name in os.listdir(self.backup_dir):
            if name.endswith(".json"):
                backup_id = name[:-5]
                backups.append(backup_id)
        return sorted(backups)

    def delete_backup(self, backup_id: str) -> None:
        """Deletes a backup snapshot file safely if it exists.

        Args:
            backup_id: Identifier of the backup snapshot.

        Raises:
            FileNotFoundError: If the specified backup file does not exist.
        """
        if not backup_id or not isinstance(backup_id, str) or not backup_id.strip():
            raise ValueError("Backup Violation: backup_id must be a non-empty string.")

        backup_filename = f"{backup_id}.json"
        filepath = os.path.join(self.backup_dir, backup_filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Backup Error: Snapshot '{backup_id}' not found for deletion.")

        os.remove(filepath)
