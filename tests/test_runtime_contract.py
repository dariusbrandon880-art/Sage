"""SAGE Runtime Application Startup Contract Tests."""

import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_runtime_app_export_contract():
    """Verify that sage.runtime:app is exported and resolves to the FastAPI application correctly."""
    from sage.runtime import app

    assert isinstance(app, FastAPI)
    assert app.title == "SAGE Runtime API"


def test_object_identity_consistency():
    """Verify that successive imports or accesses of sage.runtime.app return the identical object reference."""
    import sage.runtime

    app_first = getattr(sage.runtime, "app")
    app_second = getattr(sage.runtime, "app")

    assert app_first is app_second
    assert id(app_first) == id(app_second)


def test_import_stability_no_lazy_trigger():
    """Verify that importing other components from sage.runtime does not pre-maturely import or initialize 'app'."""
    to_delete = ["sage.runtime", "sage.api"]
    for mod in to_delete:
        if mod in sys.modules:
            del sys.modules[mod]

    import sage.runtime

    assert "app" not in sage.runtime.__dict__

    assert hasattr(sage.runtime, "check_health")
    assert "app" not in sage.runtime.__dict__

    app_obj = sage.runtime.app
    assert isinstance(app_obj, FastAPI)
    assert "app" in sage.runtime.__dict__


def test_startup_behavior_responsive():
    """Verify that the exported app starts correctly and responds to health and root queries."""
    from sage.runtime import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "SAGE Runtime online"

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] in ("healthy", "degraded", "unhealthy")
