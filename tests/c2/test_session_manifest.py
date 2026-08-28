from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.build_session_manifest import materialize


def test_manifest_materializes_live_head_and_required_surfaces(tmp_path: Path) -> None:
    output = tmp_path / "session_manifest.json"
    payload = materialize("C2-OPS-003", ["chatgpt", "gemini", "jules"], output)
    assert payload["canonical_git_sha"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    assert payload["required_interfaces"] == ["chatgpt", "gemini", "jules"]
    assert set(payload["surfaces"]) == {"chatgpt", "gemini", "jules"}
    assert all(surface["verdict"] == "PENDING" for surface in payload["surfaces"].values())
    assert all(surface["evidence_ref"] is None for surface in payload["surfaces"].values())
    assert json.loads(output.read_text()) == payload


def test_manifest_rejects_duplicate_interfaces(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(SystemExit, match="unique"):
        materialize("C2-OPS-003", ["chatgpt", "chatgpt"], tmp_path / "manifest.json")
