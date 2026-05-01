"""
ElectaVerse — Pytest Configuration & Shared Fixtures
Provides reusable test client and authentication helpers.
"""

import sys
import os
import pytest

# Ensure backend root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app  # noqa: E402


@pytest.fixture
def app():
    """Create a configured Flask test application."""
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Provide a Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Provide a Flask CLI test runner."""
    return app.test_cli_runner()
