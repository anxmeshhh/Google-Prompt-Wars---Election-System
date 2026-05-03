import sys
import os
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gcloud_ai_service import GCloudAIService
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestGCloudAIService:

    @patch('services.gcloud_ai_service.translate.Client')
    @patch('services.gcloud_ai_service.language_v2.LanguageServiceClient')
    @patch('services.gcloud_ai_service.texttospeech.TextToSpeechClient')
    def test_initialization(self, mock_tts, mock_nlp, mock_translate):
        service = GCloudAIService()
        assert service.translate_client is not None
        assert service.nlp_client is not None
        assert service.tts_client is not None

    @patch('services.gcloud_ai_service.translate.Client')
    def test_translate_text(self, mock_translate):
        mock_instance = MagicMock()
        mock_instance.translate.return_value = {'translatedText': 'नमस्ते'}
        mock_translate.return_value = mock_instance

        service = GCloudAIService()
        result = service.translate_text("Hello")
        assert result == 'नमस्ते'
        mock_instance.translate.assert_called_with("Hello", target_language='hi')

    @patch('services.gcloud_ai_service.language_v2.LanguageServiceClient')
    def test_analyze_sentiment(self, mock_nlp):
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.document_sentiment.score = 0.8
        mock_response.document_sentiment.magnitude = 0.9
        mock_instance.analyze_sentiment.return_value = mock_response
        mock_nlp.return_value = mock_instance

        service = GCloudAIService()
        result = service.analyze_sentiment("This is great!")
        assert result['score'] == 0.8
        assert result['magnitude'] == 0.9

    @patch('services.gcloud_ai_service.texttospeech.TextToSpeechClient')
    def test_synthesize_speech(self, mock_tts):
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b'audio_data'
        mock_instance.synthesize_speech.return_value = mock_response
        mock_tts.return_value = mock_instance

        service = GCloudAIService()
        result = service.synthesize_speech("Hello World")
        assert result == b'audio_data'

class TestGCloudAIRoutes:

    @patch('routes.gcloud_ai_routes.gcloud_ai.translate_text')
    def test_translate_route(self, mock_translate, client):
        mock_translate.return_value = 'नमस्ते'
        response = client.post('/api/ai/translate', json={'text': 'Hello'})
        assert response.status_code == 200
        assert json.loads(response.data)['translated'] == 'नमस्ते'

    def test_translate_route_missing_data(self, client):
        response = client.post('/api/ai/translate', json={})
        assert response.status_code == 400

    @patch('routes.gcloud_ai_routes.gcloud_ai.analyze_sentiment')
    def test_sentiment_route(self, mock_sentiment, client):
        mock_sentiment.return_value = {'score': 0.5, 'magnitude': 0.5}
        response = client.post('/api/ai/sentiment', json={'text': 'Okay'})
        assert response.status_code == 200
        assert json.loads(response.data)['sentiment']['score'] == 0.5

    def test_sentiment_route_missing_data(self, client):
        response = client.post('/api/ai/sentiment', json={})
        assert response.status_code == 400

    @patch('routes.gcloud_ai_routes.gcloud_ai.synthesize_speech')
    def test_tts_route(self, mock_tts, client):
        mock_tts.return_value = b'audio'
        response = client.post('/api/ai/tts', json={'text': 'Hello'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'audio' in data
        assert data['audio'].startswith('data:audio/mp3;base64,')

    def test_tts_route_missing_data(self, client):
        response = client.post('/api/ai/tts', json={})
        assert response.status_code == 400
