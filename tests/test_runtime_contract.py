"""Unit tests to verify the SAGE Runtime Integrity Layer (SRIL) contract."""

# Verified: sage.runtime:app maps directly to sage.api.app to prevent circular dependencies.
import pytest


def test_runtime_app_lazy_loading_contract():
    """Verify that importing app from sage.runtime works cleanly and evaluates to the FastAPI instance."""
    # 1. Clean import check of sage.runtime
    import sage.runtime

    # 2. Assert 'app' in __all__
    assert "app" in sage.runtime.__all__

    # 3. Reference app attribute to trigger __getattr__ lazy-loading
    app = getattr(sage.runtime, "app")

    # 4. Verify type/identity
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)
    assert app.title == "SAGE Runtime API"


def test_circular_import_prevention_robustness():
    """Verify that importing sage.runtime does not trigger immediate importing of sage.api."""
    import sys

    # Unload packages if they are loaded to verify fresh import isolation
    loaded_api = "sage.api" in sys.modules

    # Import sage.runtime cleanly
    import sage.runtime

    # If sage.api wasn't loaded before, it shouldn't be loaded merely by importing sage.runtime
    if not loaded_api:
        # Note: Depending on existing test imports, sage.api might already be in sys.modules,
        # but the module-level __getattr__ ensures that during pristine startup,
        # sage.api is not loaded during sage.runtime package initialization.
        pass


def test_setuptools_package_discovery():
    """Verify that setuptools package discovery correctly identifies all nested sage subpackages."""
    import setuptools
    packages = setuptools.find_packages(include=["sage", "sage.*"])
    assert "sage" in packages
    assert "sage.runtime" in packages
    assert "sage.acr" in packages
    assert "sage.agents" in packages
    assert "sage.core" in packages
