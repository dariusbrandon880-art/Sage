import os
import json
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

# Prep path for scripts import
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_openai_runtime_activation import run_openai_activation


def test_run_openai_activation_quota_exhausted(tmp_path):
    """Test that OpenAI quota exhaustion is handled as a recoverable failure, records evidence, and exits cleanly with 0."""
    evidence_file = tmp_path / "openai_runtime_live_connection.json"
    production_activation_file = tmp_path / "chatgpt_live_runtime_production_activation.json"

    # Setup environment variables
    env_mock = {
        "OPENAI_API_KEY": "sk-proj-testkey",
        "SAGE_AGENT_ID": "chatgpt-runtime-agent",
        "SAGE_RUNTIME_ENDPOINT": "http://localhost:8000",
        "SAGE_AUTH_SECRET": "test_secret_key"
    }

    # Mock response from OpenAI
    mock_res = MagicMock()
    mock_res.status_code = 429
    mock_res.text = "insufficient_quota: You exceeded your current quota, please check your plan and billing details."

    def mock_sys_exit(code):
        raise SystemExit(code)

    with patch.dict(os.environ, env_mock), \
         patch("httpx.post", return_value=mock_res) as mock_post, \
         patch("sys.exit", side_effect=mock_sys_exit) as mock_exit, \
         patch("scripts.run_openai_runtime_activation.os.makedirs") as mock_makedirs, \
         patch("builtins.open") as mock_open:

        # Intercept written files
        written_contents = {}

        def mock_open_side_effect(filepath, mode="r", encoding=None):
            # Create a mock file object
            file_mock = MagicMock()

            # Intercept write
            path_str = str(filepath)
            if path_str not in written_contents:
                written_contents[path_str] = []

            def write_content(content):
                written_contents[path_str].append(content)

            file_mock.write = write_content
            # Suppress context manager block behavior
            file_mock.__enter__.return_value = file_mock
            return file_mock

        mock_open.side_effect = mock_open_side_effect

        # Run the activation script (should raise SystemExit(0))
        with pytest.raises(SystemExit) as exc_info:
            run_openai_activation()

        # Verify exit code was 0 (clean exit)
        assert exc_info.value.code == 0

        # Verify mock post was called
        mock_post.assert_called_once()

        # Check recorded evidence capture payload
        assert "evidence_capture/openai_runtime_live_connection.json" in written_contents
        assert "evidence_capture/chatgpt_live_runtime_production_activation.json" in written_contents

        # Parse written JSON
        evidence_str = "".join(written_contents["evidence_capture/openai_runtime_live_connection.json"])
        evidence_json = json.loads(evidence_str)
        assert evidence_json["authentication_result"] == "RECOVERABLE_EXTERNAL_FAILURE"
        assert evidence_json["execution_result"]["completion_status"] == "RECOVERABLE_EXTERNAL_FAILURE"
        assert "Quota/Credit" in evidence_json["execution_result"]["error"]
        assert evidence_json["validation_result"]["status"] == "VALIDATED_WITH_RECOVERABLE_FAILURE"
        assert evidence_json["validation_result"]["is_compliant"] is True
        assert "recoverable external dependency failure" in evidence_json["recovery_remediation"].lower()
