import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_language_client = None
_is_available = False

def init_nlp() -> bool:
    """Initialize the Google Cloud Natural Language client."""
    global _language_client, _is_available
    
    if _language_client is not None:
        return True
        
    try:
        from google.cloud import language_v1
        
        # In a real environment, this uses GOOGLE_APPLICATION_CREDENTIALS
        _language_client = language_v1.LanguageServiceClient()
        _is_available = True
        logger.info("✅ Google Cloud Natural Language API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Google Cloud NLP: {str(e)}")
        _is_available = False
        return False

def is_nlp_available() -> bool:
    """Check if NLP service is available."""
    if _language_client is None and not _is_available:
        init_nlp()
    return _is_available

def analyze_sentiment(text: str) -> Optional[Dict]:
    """
    Analyze the sentiment of a given text.
    Returns a dict with score and magnitude, or None if unavailable.
    """
    if not is_nlp_available():
        return None
        
    try:
        from google.cloud import language_v1
        document = language_v1.Document(
            content=text, type_=language_v1.Document.Type.PLAIN_TEXT
        )
        sentiment = _language_client.analyze_sentiment(
            request={"document": document}
        ).document_sentiment

        return {
            "score": sentiment.score,
            "magnitude": sentiment.magnitude
        }
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        return None
