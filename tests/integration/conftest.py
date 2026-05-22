"""Fixtures for Home Assistant-dependent tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading the custom integration during tests."""
    yield
