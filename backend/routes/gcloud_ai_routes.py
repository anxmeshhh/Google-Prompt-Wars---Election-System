import base64
from flask import Blueprint, request, jsonify
from services.gcloud_ai_service import GCloudAIService
import logging

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger('electaverse.ai_routes')
gcloud_ai = GCloudAIService()

@ai_bp.route('/api/ai/translate', methods=['POST'])
def translate_text():
    """Endpoint for Cloud Translation API."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text parameter'}), 400
        
    text = data['text']
    target = data.get('target', 'hi')  # Default to Hindi
    
    translated = gcloud_ai.translate_text(text, target)
    return jsonify({'translated': translated})

@ai_bp.route('/api/ai/sentiment', methods=['POST'])
def analyze_sentiment():
    """Endpoint for Cloud Natural Language API."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text parameter'}), 400
        
    text = data['text']
    sentiment = gcloud_ai.analyze_sentiment(text)
    return jsonify({'sentiment': sentiment})

@ai_bp.route('/api/ai/tts', methods=['POST'])
def generate_speech():
    """Endpoint for Cloud Text-to-Speech API."""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text parameter'}), 400
        
    text = data['text']
    audio_bytes = gcloud_ai.synthesize_speech(text)
    
    if not audio_bytes:
        return jsonify({'error': 'TTS failed or offline'}), 500
        
    # Return base64 encoded MP3
    encoded = base64.b64encode(audio_bytes).decode('utf-8')
    return jsonify({
        'audio': f"data:audio/mp3;base64,{encoded}"
    })
