from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts import build_session_manifest, verify_session_rehydration_contract


def test_materialize_binds_current_head_and_canonical_main(monkeypatch, tmp_path):
    monkeypatch.setattr(build_session_manifest, "git_head", lambda: "a" * 40)
    monkeypatch.setattr(build_session_manifest, "canonical_main_head", lambda: "b" * 40)
    monkeypatch.setattr(build_session_manifest, "active_branch", lambda: "test-branch")

    manifest = build_session_manifest.materialize(
        mission="TEST_MISSION",
        interfaces=["CHATGPT_C2", "JULES_ENGINEER"],
        output=tmp_path / "session_manifest.json",
    )

    assert manifest["canonical_git_sha"] == "a" * 40
    assert manifest["canonical_main_sha"] == "b" * 40


def test_verify_fails_closed_on_main_drift(monkeypatch, tmp_path):
    manifest_path = tmp_path / "session_manifest.json"
    schema_path = tmp_path / "SAGE_SESSION_STATE_MANIFEST.json"
    manifest_path.write_text(
        '{"canonical_git_sha":"' + "a" * 40 + '","canonical_main_sha":"' + "b" * 40 + '","active_mission":"M","required_interfaces":["I"],"surfaces":{"I":{"verdict":"PENDING","evidence_ref":null}},"identity_contract":{"nameplate":"n","hud":"h","immersion_doctrine":"d"},"binding":{"drift_policy":"FAIL_CLOSED"}}\n',
        encoding="utf-8",
    )
    schema_path.write_text('{"binding":{"sha_required":true}}\n', encoding="utf-8")
    for name in ("n", "h", "d"):
        (tmp_path / name).write_text("ok", encoding="utf-8")

    monkeypatch.setattr(verify_session_rehydration_contract, "MANIFEST", manifest_path)
    monkeypatch.setattr(verify_session_rehydration_contract, "SCHEMA", schema_path)
    monkeypatch.setattr(verify_session_rehydration_contract, "head", lambda: "a" * 40)
    monkeypatch.setattr(verify_session_rehydration_contract, "canonical_main_head", lambda: "c" * 40)

    with pytest.raises(SystemExit, match="main SHA"):
        verify_session_rehydration_contract.main()


def test_canonical_main_head_fails_closed_when_remote_ref_missing(monkeypatch):
    def missing(*args, **kwargs):
        raise verify_session_rehydration_contract.subprocess.CalledProcessError(128, args[0])

    monkeypatch.setattr(verify_session_rehydration_contract.subprocess, "check_output", missing)

    with pytest.raises(SystemExit, match="origin/main ref is unavailable"):
        verify_session_rehydration_contract.canonical_main_head()
