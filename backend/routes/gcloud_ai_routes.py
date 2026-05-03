import base64
from flask import Blueprint, request, jsonify
from services.gcloud_ai_service import GCloudAIService
from services.gcloud_vision_service import GCloudVisionService
from services.gcloud_secret_service import GCloudSecretService
import logging

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger('electaverse.ai_routes')
gcloud_ai = GCloudAIService()
gcloud_vision = GCloudVisionService()
gcloud_secrets = GCloudSecretService()

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

@ai_bp.route('/api/ai/vision/safety', methods=['POST'])
def analyze_image_safety():
    """Endpoint for Cloud Vision API — content moderation."""
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'Missing image parameter (base64)'}), 400
    
    try:
        image_bytes = base64.b64decode(data['image'])
    except Exception:
        return jsonify({'error': 'Invalid base64 image data'}), 400
    
    result = gcloud_vision.analyze_image_safety(image_bytes)
    return jsonify({'safety': result})

@ai_bp.route('/api/ai/vision/ocr', methods=['POST'])
def detect_text_in_image():
    """Endpoint for Cloud Vision API — OCR text detection."""
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'error': 'Missing image parameter (base64)'}), 400
    
    try:
        image_bytes = base64.b64decode(data['image'])
    except Exception:
        return jsonify({'error': 'Invalid base64 image data'}), 400
    
    text = gcloud_vision.detect_text_in_image(image_bytes)
    return jsonify({'text': text})

@ai_bp.route('/api/ai/services', methods=['GET'])
def list_ai_services():
    """List all available Google Cloud AI services and their status."""
    return jsonify({
        'services': {
            'translation': {'status': 'active' if gcloud_ai.translate_client else 'offline'},
            'natural_language': {'status': 'active' if gcloud_ai.nlp_client else 'offline'},
            'text_to_speech': {'status': 'active' if gcloud_ai.tts_client else 'offline'},
            'vision': {'status': 'active' if gcloud_vision.client else 'offline'},
            'secret_manager': {'status': 'active' if gcloud_secrets.client else 'offline'},
        }
    })

