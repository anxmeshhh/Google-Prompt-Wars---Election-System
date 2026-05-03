"""
ElectaVerse — Content Routes Tests
Tests for content API endpoints (timeline, voter guide, phases).
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


class TestContentEndpoints:
    """Tests for the content API routes."""

    def test_timeline_returns_200(self, client):
        rv = client.get('/api/content/timeline')
        assert rv.status_code == 200

    def test_voter_guide_returns_200(self, client):
        rv = client.get('/api/content/voter-guide')
        assert rv.status_code == 200

    def test_phases_returns_200(self, client):
        rv = client.get('/api/content/phases')
        assert rv.status_code == 200


class TestAIServicesEndpoint:
    """Tests for the AI services status endpoint."""

    def test_ai_services_list(self, client):
        rv = client.get('/api/ai/services')
        assert rv.status_code == 200
        data = rv.get_json()
        assert 'services' in data
        assert 'translation' in data['services']
        assert 'natural_language' in data['services']
        assert 'text_to_speech' in data['services']
        assert 'vision' in data['services']
        assert 'secret_manager' in data['services']


class TestVisionRoutes:
    """Tests for the Cloud Vision API routes."""

    def test_vision_safety_missing_data(self, client):
        rv = client.post('/api/ai/vision/safety', json={})
        assert rv.status_code == 400

    def test_vision_ocr_missing_data(self, client):
        rv = client.post('/api/ai/vision/ocr', json={})
        assert rv.status_code == 400

    def test_vision_safety_invalid_base64(self, client):
        rv = client.post('/api/ai/vision/safety', json={'image': '!!!invalid!!!'})
        assert rv.status_code == 400

    def test_vision_ocr_invalid_base64(self, client):
        rv = client.post('/api/ai/vision/ocr', json={'image': '!!!invalid!!!'})
        assert rv.status_code == 400
