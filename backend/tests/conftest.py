"""
ElectaVerse — Pytest Configuration & Shared Fixtures
Provides reusable test client, authentication helpers, and mock services.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

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


@pytest.fixture
def auth_headers():
    """Create valid JWT auth headers for authenticated test requests."""
    from services.security import create_access_token
    token = create_access_token(user_id=1, role='voter')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def admin_headers():
    """Create valid JWT auth headers for admin (official) test requests."""
    from services.security import create_access_token
    token = create_access_token(user_id=1, role='official')
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


@pytest.fixture
def mock_gemini():
    """Patch GeminiService to return deterministic responses."""
    with patch('services.gemini_service.GeminiService') as MockGemini:
        instance = MagicMock()
        instance.is_available.return_value = True
        instance.generate.return_value = "This is a mock AI response."
        instance.generate_json.return_value = '{"mock": true}'
        instance.count_tokens.return_value = 42
        instance.list_available_models.return_value = ['models/gemini-2.5-flash']
        instance.get_model_info.return_value = {
            'model_name': 'gemini-2.5-flash',
            'configured': True,
            'groq_fallback': False,
            'groq_model': None,
        }
        MockGemini.return_value = instance
        yield instance


@pytest.fixture
def sample_booth():
    """Create a sample Booth instance for testing."""
    from models.booth import Booth
    return Booth(
        id='BOOTH-DEL-001',
        name='New Delhi Booth #1',
        constituency='New Delhi',
        lat=28.6139,
        lng=77.2090,
        queue_length=25,
        throughput_rate=25.0,
        registered_voters=1200,
    )


@pytest.fixture
def sample_incident():
    """Create a sample Incident instance for testing."""
    from models.incident import Incident
    return Incident(
        booth_id='BOOTH-DEL-001',
        booth_name='New Delhi Booth #1',
        constituency='New Delhi',
        incident_type='EVM_MALFUNCTION',
        severity='critical',
        description='EVM unit not responding to button presses',
        status='open',
    )

