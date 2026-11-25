"""Existing behavior tests focus on application behavior, not auth middleware."""
import pytest


@pytest.fixture(autouse=True)
def isolate_access_control_in_legacy_tests(monkeypatch):
    # Auth enforcement is tested explicitly in test_auth.py.
    monkeypatch.setattr("app.main.authenticated", lambda request: True)
