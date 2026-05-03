"""
ElectaVerse — Vision & Secret Manager Service Tests
Tests for Cloud Vision and Secret Manager services with graceful fallback.
All tests run without real cloud credentials.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ═══════════════════════════════════════════
# Cloud Vision Service Tests
# ═══════════════════════════════════════════

class TestGCloudVisionService:
    """Test Cloud Vision service with graceful degradation."""

    @patch('services.gcloud_vision_service.vision.ImageAnnotatorClient')
    def test_initialization(self, mock_client):
        from services.gcloud_vision_service import GCloudVisionService
        service = GCloudVisionService()
        assert service.client is not None

    @patch('services.gcloud_vision_service.vision.ImageAnnotatorClient')
    def test_analyze_image_safety(self, mock_client):
        from services.gcloud_vision_service import GCloudVisionService
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.safe_search_annotation.adult = 1
        mock_response.safe_search_annotation.violence = 1
        mock_response.safe_search_annotation.racy = 1
        mock_instance.safe_search_detection.return_value = mock_response
        mock_client.return_value = mock_instance

        service = GCloudVisionService()
        result = service.analyze_image_safety(b'fake_image_data')
        assert 'safe' in result

    @patch('services.gcloud_vision_service.vision.ImageAnnotatorClient')
    def test_detect_text_in_image(self, mock_client):
        from services.gcloud_vision_service import GCloudVisionService
        mock_instance = MagicMock()
        mock_text = MagicMock()
        mock_text.description = "Vote for Democracy"
        mock_response = MagicMock()
        mock_response.text_annotations = [mock_text]
        mock_instance.text_detection.return_value = mock_response
        mock_client.return_value = mock_instance

        service = GCloudVisionService()
        result = service.detect_text_in_image(b'fake_image_data')
        assert result == "Vote for Democracy"

    @patch('services.gcloud_vision_service.vision.ImageAnnotatorClient')
    def test_detect_labels(self, mock_client):
        from services.gcloud_vision_service import GCloudVisionService
        mock_instance = MagicMock()
        mock_label = MagicMock()
        mock_label.description = "ballot box"
        mock_label.score = 0.95
        mock_response = MagicMock()
        mock_response.label_annotations = [mock_label]
        mock_instance.label_detection.return_value = mock_response
        mock_client.return_value = mock_instance

        service = GCloudVisionService()
        result = service.detect_labels(b'fake_image_data')
        assert len(result) == 1
        assert result[0]['label'] == 'ballot box'

    def test_safety_without_client(self):
        from services.gcloud_vision_service import GCloudVisionService
        service = GCloudVisionService.__new__(GCloudVisionService)
        service.client = None
        service.executor = MagicMock()
        result = service.analyze_image_safety(b'data')
        assert result['safe'] is True

    def test_ocr_without_client(self):
        from services.gcloud_vision_service import GCloudVisionService
        service = GCloudVisionService.__new__(GCloudVisionService)
        service.client = None
        service.executor = MagicMock()
        result = service.detect_text_in_image(b'data')
        assert result == ""

    def test_labels_without_client(self):
        from services.gcloud_vision_service import GCloudVisionService
        service = GCloudVisionService.__new__(GCloudVisionService)
        service.client = None
        service.executor = MagicMock()
        result = service.detect_labels(b'data')
        assert result == []


# ═══════════════════════════════════════════
# Secret Manager Service Tests
# ═══════════════════════════════════════════

class TestGCloudSecretService:
    """Test Secret Manager service with graceful degradation."""

    @patch('services.gcloud_secret_service.secretmanager.SecretManagerServiceClient')
    def test_initialization(self, mock_client):
        from services.gcloud_secret_service import GCloudSecretService
        service = GCloudSecretService()
        assert service.client is not None

    def test_get_secret_fallback_to_env(self, monkeypatch):
        from services.gcloud_secret_service import GCloudSecretService
        monkeypatch.setenv('MY_SECRET', 'env_value')
        service = GCloudSecretService.__new__(GCloudSecretService)
        service.client = None
        service.project_id = 'test'
        result = service.get_secret('MY_SECRET')
        assert result == 'env_value'

    def test_secret_exists_without_client(self):
        from services.gcloud_secret_service import GCloudSecretService
        service = GCloudSecretService.__new__(GCloudSecretService)
        service.client = None
        service.project_id = 'test'
        assert service.secret_exists('any_secret') is False

    def test_list_secrets_without_client(self):
        from services.gcloud_secret_service import GCloudSecretService
        service = GCloudSecretService.__new__(GCloudSecretService)
        service.client = None
        service.project_id = 'test'
        assert service.list_secrets() == []

    @patch('services.gcloud_secret_service.secretmanager.SecretManagerServiceClient')
    def test_get_secret_from_manager(self, mock_client):
        from services.gcloud_secret_service import GCloudSecretService
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.payload.data = b'secret_value_123'
        mock_instance.access_secret_version.return_value = mock_response
        mock_client.return_value = mock_instance

        service = GCloudSecretService()
        result = service.get_secret('API_KEY')
        assert result == 'secret_value_123'
