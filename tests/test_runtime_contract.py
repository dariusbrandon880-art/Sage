"""SAGE Runtime Application Startup Contract Tests."""

def test_runtime_app_export_contract():
    """Verify that sage.runtime:app is exported and resolves to the FastAPI application correctly."""
    from sage.runtime import app
    from fastapi import FastAPI

    assert isinstance(app, FastAPI)
    assert app.title == "SAGE Runtime API"
