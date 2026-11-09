"""The admin test setup (sqlite engines, token 'test-token', no LLM / live markets) for the trend tab routes."""
from tests.admin.conftest import _sqlite_engines, admin_client  # noqa: F401


import pytest


@pytest.fixture(autouse=True)
def _guest_view_off(monkeypatch):
    """The Mac .env may switch the read-only guest view on — tests start with it off."""
    monkeypatch.setattr("app.admin.routes.guest_trends_on", lambda: False)
