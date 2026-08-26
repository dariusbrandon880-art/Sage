import subprocess

from sage.c2.flight_gps.adapters.github import GitHubTelemetryAdapter
from sage.c2.flight_gps.adapters.git import GitTelemetryAdapter
from sage.c2.flight_gps.adapters.base import TelemetryException
from sage.c2.flight_gps.dependency_graph import DependencyGraphAnalyzer
from sage.c2.flight_gps.models import ObservabilityState


def test_github_adapter_reports_degraded_on_cli_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])

    monkeypatch.setattr(subprocess, "run", fail)
    manifests, state = GitHubTelemetryAdapter().fetch_active_manifests()
    assert manifests == []
    assert state == ObservabilityState.DEGRADED


def test_git_adapter_reports_offline_when_git_unavailable(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("git unavailable")

    monkeypatch.setattr(subprocess, "run", fail)
    manifests, state = GitTelemetryAdapter().fetch_active_manifests()
    assert manifests == []
    assert state == ObservabilityState.OFFLINE


def test_dependency_graph_extracts_symbols_and_imports():
    graph = DependencyGraphAnalyzer().extract(
        "import pathlib\nfrom sage.c2 import router\nclass Example: pass\ndef run(): pass\n"
    )
    assert {"Example", "run"} <= graph["symbols"]
    assert {"pathlib", "sage.c2"} <= graph["modules"]
