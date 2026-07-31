"""SAGE Experimental State Backup and Rehydration Tests."""

import os
import json
import pytest
import shutil
from sage.experimental.act.persistence import StateBackupManager


@pytest.fixture
def temp_backup_dir():
    """Fixture providing a temporary backup directory for state snapshots."""
    test_dir = "sage_data/test_backups"
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_backup_and_restore_success(temp_backup_dir):
    """Verify that state can be serialized, backed up, and successfully rehydrated with valid checksum."""
    manager = StateBackupManager(backup_dir=temp_backup_dir)

    state_dict = {
        "active_session": "session_a1b2c3d4",
        "timestamp": "2026-07-30T12:00:00Z",
        "decisions": ["decision_001", "decision_002"],
        "metrics": {"total_calls": 42, "healthy": True},
    }

    # Backup the state
    backup_id = "state_snap_001"
    filepath = manager.backup_state(state_dict, backup_id)

    assert os.path.exists(filepath)
    assert backup_id in manager.list_backups()

    # Rehydrate the state
    restored_payload = manager.restore_state(backup_id)
    assert restored_payload == state_dict


def test_backup_validation_errors(temp_backup_dir):
    """Verify that invalid inputs to backup or restore throw errors."""
    manager = StateBackupManager(backup_dir=temp_backup_dir)

    with pytest.raises(ValueError, match="backup_id must be a non-empty string"):
        manager.backup_state({}, "")

    with pytest.raises(ValueError, match="state_dict must be a dictionary"):
        manager.backup_state([], "valid_id")

    with pytest.raises(ValueError, match="backup_id must be a non-empty string"):
        manager.restore_state("   ")


def test_restore_nonexistent_fails(temp_backup_dir):
    """Verify that attempting to restore a nonexistent snapshot throws a FileNotFoundError."""
    manager = StateBackupManager(backup_dir=temp_backup_dir)
    with pytest.raises(FileNotFoundError, match="not found"):
        manager.restore_state("missing_snap_999")


def test_tamper_corruption_detection(temp_backup_dir):
    """Verify that modifying the payload triggers a SHA-256 checksum validation error."""
    manager = StateBackupManager(backup_dir=temp_backup_dir)

    state_dict = {"secret_code": 42}
    backup_id = "snap_tamper"
    filepath = manager.backup_state(state_dict, backup_id)

    # Corrupt the file payload manually
    with open(filepath, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    # Change the payload internally without updating the checksum header
    envelope["payload"]["secret_code"] = 999

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(envelope, f)

    # Attempting to restore must throw checksum mismatch ValueError
    with pytest.raises(ValueError, match="SHA-256 checksum mismatch detected"):
        manager.restore_state(backup_id)


def test_malformed_json_rejection(temp_backup_dir):
    """Verify that a malformed JSON file is rejected upon restore attempt."""
    manager = StateBackupManager(backup_dir=temp_backup_dir)

    backup_id = "snap_malformed"
    filepath = os.path.join(temp_backup_dir, f"{backup_id}.json")

    # Write truncated/malformed JSON
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("{malformed JSON content")

    with pytest.raises(ValueError, match="Malformed JSON structure"):
        manager.restore_state(backup_id)


def test_delete_and_list_backups(temp_backup_dir):
    """Verify that snapshots can be listed and deleted correctly."""
    manager = StateBackupManager(backup_dir=temp_backup_dir)

    assert manager.list_backups() == []

    manager.backup_state({"v": 1}, "snap_a")
    manager.backup_state({"v": 2}, "snap_b")

    assert manager.list_backups() == ["snap_a", "snap_b"]

    manager.delete_backup("snap_a")
    assert manager.list_backups() == ["snap_b"]

    with pytest.raises(FileNotFoundError, match="not found for deletion"):
        manager.delete_backup("snap_a")
