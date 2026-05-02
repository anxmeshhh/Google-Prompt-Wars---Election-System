import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Lazy loaded client
_translate_client = None
_is_available = False

def init_translation() -> bool:
    """Initialize the Google Cloud Translation client."""
    global _translate_client, _is_available
    
    # Fast path if already initialized
    if _translate_client is not None:
        return True
        
    try:
        from google.cloud import translate_v2 as translate
        
        # In a real environment, this uses GOOGLE_APPLICATION_CREDENTIALS
        _translate_client = translate.Client()
        _is_available = True
        logger.info("✅ Google Cloud Translation API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Cloud Translation: {str(e)}")
        _is_available = False
        return False

def is_translation_available() -> bool:
    """Check if Translation service is available."""
    if _translate_client is None and not _is_available:
        init_translation()
    return _is_available

def translate_text(text: str, target_language: str = "hi") -> Optional[Dict]:
    """
    Translate text to a target language.
    Returns a dict with translated text and detected source language,
    or None if the service is unavailable.
    """
    if not is_translation_available():
        return None
        
    try:
        result = _translate_client.translate(text, target_language=target_language)
        return {
            "translated_text": result["translatedText"],
            "source_language": result["detectedSourceLanguage"],
            "target_language": target_language
        }
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        return None
