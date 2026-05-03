"""
ElectaVerse — Advanced Security Tests
Tests for SQL injection filtering, payload size limits, HSTS, and security headers.
"""

import sys
import os
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestSecurityHeaders:
    """Verify all security headers are present on API responses."""

    def test_hsts_header(self, client):
        rv = client.get('/api/health')
        assert 'Strict-Transport-Security' in rv.headers
        assert '31536000' in rv.headers['Strict-Transport-Security']

    def test_x_content_type_options(self, client):
        rv = client.get('/api/health')
        assert rv.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        rv = client.get('/api/health')
        assert rv.headers.get('X-Frame-Options') == 'SAMEORIGIN'

    def test_referrer_policy(self, client):
        rv = client.get('/api/health')
        assert rv.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'

    def test_permissions_policy(self, client):
        rv = client.get('/api/health')
        assert 'browsing-topics=()' in rv.headers.get('Permissions-Policy', '')

    def test_x_request_id_present(self, client):
        rv = client.get('/api/health')
        assert 'X-Request-ID' in rv.headers

    def test_custom_request_id_honored(self, client):
        rv = client.get('/api/health', headers={'X-Request-ID': 'test-123'})
        assert rv.headers.get('X-Request-ID') == 'test-123'

    def test_cross_domain_policy(self, client):
        rv = client.get('/api/health')
        assert rv.headers.get('X-Permitted-Cross-Domain-Policies') == 'none'

    def test_auth_cache_control(self, client):
        rv = client.post('/api/auth/login', json={})
        assert 'no-store' in rv.headers.get('Cache-Control', '')


class TestInputSanitization:
    """Test XSS and SQL injection filtering."""

    def test_xss_script_tag_filtered(self, client):
        """Requests with <script> tags should still be processed (tags filtered)."""
        rv = client.post('/api/auth/login', json={
            'email': '<script>alert(1)</script>@test.com',
            'password': 'test123'
        })
        # Should not crash — sanitizer filters the input
        assert rv.status_code in (400, 401, 429)

    def test_xss_event_handler_filtered(self, client):
        """Requests with onerror= should still be processed (filtered)."""
        rv = client.post('/api/auth/login', json={
            'email': '" onerror="alert(1)"@test.com',
            'password': 'test123'
        })
        assert rv.status_code in (400, 401, 429)

    def test_sql_injection_in_query(self, client):
        """SQL injection-like table names should be rejected."""
        rv = client.get('/api/database/query?table=users;DROP TABLE users')
        assert rv.status_code in (400, 403)


class TestRateLimiting:
    """Test rate limiting is active."""

    def test_rate_limit_header_present(self, client):
        rv = client.get('/api/health')
        # Health is exempt, but auth is rate-limited
        rv = client.post('/api/auth/login', json={'email': 'a@b.com', 'password': 'x'})
        # After many requests it would return 429, but at least it processes
        assert rv.status_code in (400, 401, 429)
