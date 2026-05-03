"""
ElectaVerse — API Endpoint Tests
Comprehensive test coverage for health, auth, incidents, analytics,
battle, and database routes.
"""

import pytest
import json
from unittest.mock import patch


# ─────────────────────────────────────────────
# 1. Health & Core
# ─────────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for the /api/health status endpoint."""

    def test_health_returns_200(self, client):
        """Health check should always return 200."""
        rv = client.get('/api/health')
        assert rv.status_code == 200

    def test_health_has_required_fields(self, client):
        """Health response must contain status, simulation, booths, clock."""
        rv = client.get('/api/health')
        data = rv.get_json()
        assert data['status'] == 'running'
        assert 'simulation' in data
        assert 'booths' in data
        assert 'clock' in data

    def test_health_cached(self, client):
        """Two rapid health calls should return same data (cache test)."""
        rv1 = client.get('/api/health')
        rv2 = client.get('/api/health')
        assert rv1.get_json() == rv2.get_json()


# ─────────────────────────────────────────────
# 2. Authentication
# ─────────────────────────────────────────────

class TestAuthValidation:
    """Tests for authentication input validation."""

    def test_login_missing_credentials(self, client):
        """Login with empty body should return 400."""
        rv = client.post('/api/auth/login', json={})
        assert rv.status_code == 400
        assert 'error' in rv.get_json()

    def test_login_missing_password(self, client):
        """Login with email but no password should return 400."""
        rv = client.post('/api/auth/login', json={'email': 'test@test.com'})
        assert rv.status_code == 400

    def test_login_missing_email(self, client):
        """Login with password but no email should return 400."""
        rv = client.post('/api/auth/login', json={'password': 'secret'})
        assert rv.status_code == 400

    def test_login_invalid_credentials(self, client):
        """Login with non-existent user should return 401."""
        rv = client.post('/api/auth/login', json={
            'email': 'nonexistent@fake.com',
            'password': 'wrongpassword'
        })
        assert rv.status_code == 401

    def test_register_missing_fields(self, client):
        """Registration with missing fields should return 400."""
        rv = client.post('/api/auth/register', json={'email': 'a@b.com'})
        assert rv.status_code == 400

    def test_register_short_password(self, client):
        """Registration with short password should return 400."""
        rv = client.post('/api/auth/register', json={
            'name': 'Test',
            'email': 'test@short.com',
            'password': '123'
        })
        assert rv.status_code == 400
        assert 'at least 6' in rv.get_json()['error']

    def test_me_unauthenticated(self, client):
        """GET /me without token should return 401."""
        rv = client.get('/api/auth/me')
        assert rv.status_code == 401

    def test_me_invalid_token(self, client):
        """GET /me with garbage token should return 401."""
        rv = client.get('/api/auth/me', headers={
            'Authorization': 'Bearer invalidtoken123'
        })
        assert rv.status_code == 401

    def test_logout_without_token(self, client):
        """Logout without token should still succeed gracefully."""
        rv = client.post('/api/auth/logout')
        assert rv.status_code == 200


class TestGoogleAuth:
    """Tests for Google OAuth endpoint validation."""

    def test_google_login_missing_token(self, client):
        """Google login without token should return 400."""
        rv = client.post('/api/auth/google', json={})
        assert rv.status_code == 400
        assert 'Token is required' in rv.get_json()['error']

    @patch('routes.auth_routes.id_token.verify_oauth2_token')
    def test_google_login_invalid_token(self, mock_verify, client):
        """Google login with fake token should return 401."""
        mock_verify.side_effect = ValueError('Invalid token')
        rv = client.post('/api/auth/google', json={'token': 'fake.jwt.token'})
        assert rv.status_code == 401


# ─────────────────────────────────────────────
# 3. Battle / Prompt Wars
# ─────────────────────────────────────────────

class TestBattleEndpoint:
    """Tests for the Prompt Wars battle API."""

    def test_battle_missing_topic(self, client):
        """Starting a battle without a topic should return 400."""
        rv = client.post('/api/battle/start', json={})
        assert rv.status_code == 400
        assert 'topic' in rv.get_json()['error'].lower()


# ─────────────────────────────────────────────
# 4. Database Explorer
# ─────────────────────────────────────────────

class TestDatabaseRoutes:
    """Tests for the database exploration API (admin-only access)."""

    def test_tables_endpoint(self, client):
        """GET /api/database/tables without admin auth should return 403."""
        rv = client.get('/api/database/tables')
        assert rv.status_code == 403

    def test_query_missing_table(self, client):
        """Query without admin auth should return 403."""
        rv = client.get('/api/database/query')
        assert rv.status_code == 403

    def test_query_invalid_table(self, client):
        """Query with SQL-injection-like table name should return 403 (no auth)."""
        rv = client.get('/api/database/query?table=; DROP TABLE users;')
        assert rv.status_code == 403


# ─────────────────────────────────────────────
# 5. Analytics
# ─────────────────────────────────────────────

class TestAnalytics:
    """Tests for the analytics endpoints."""

    def test_turnout_endpoint(self, client):
        """GET /api/analytics/turnout should return 200."""
        rv = client.get('/api/analytics/turnout')
        assert rv.status_code == 200
        assert 'timeline' in rv.get_json()

    def test_incidents_analytics(self, client):
        """GET /api/analytics/incidents should return grouped data."""
        rv = client.get('/api/analytics/incidents')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'by_type' in data
        assert 'by_severity' in data

    def test_queue_analytics(self, client):
        """GET /api/analytics/queues should return distribution."""
        rv = client.get('/api/analytics/queues')
        assert rv.status_code in (200, 503)


# ─────────────────────────────────────────────
# 6. Incident Reporting
# ─────────────────────────────────────────────

class TestIncidents:
    """Tests for the incident management API."""

    def test_get_incidents(self, client):
        """GET /api/incidents should return incident list."""
        rv = client.get('/api/incidents')
        assert rv.status_code == 200
        assert 'incidents' in rv.get_json()

    def test_report_incident_missing_fields(self, client):
        """POST /api/incidents without required fields should return 400."""
        rv = client.post('/api/incidents', json={})
        assert rv.status_code == 400


# ─────────────────────────────────────────────
# 7. Chat
# ─────────────────────────────────────────────

class TestChat:
    """Tests for the AI chat API."""

    def test_chat_unauthenticated(self, client):
        """POST /api/chat without auth should return 401."""
        rv = client.post('/api/chat', json={'message': 'hello'})
        assert rv.status_code == 401

    def test_chat_history_unauthenticated(self, client):
        """GET /api/chat/history without auth should return 401."""
        rv = client.get('/api/chat/history')
        assert rv.status_code == 401
