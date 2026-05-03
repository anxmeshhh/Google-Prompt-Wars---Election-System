import logging
from config import Config
from google.cloud import translate_v2 as translate
from google.cloud import language_v2
from google.cloud import texttospeech
from google.api_core.exceptions import GoogleAPIError
import concurrent.futures

logger = logging.getLogger('electaverse.gcloud_ai')

class GCloudAIService:
    """Wrapper for Google Cloud Translate, Natural Language, and Text-to-Speech APIs."""
    
    def __init__(self):
        # Thread pool to prevent C-extension network calls from blocking Eventlet
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
        # We catch credential errors silently if running locally without ADC
        self.translate_client = None
        self.nlp_client = None
        self.tts_client = None
        
        try:
            # Initialize clients. These will automatically pick up the credentials
            # from the GCE instance metadata or GOOGLE_APPLICATION_CREDENTIALS.
            self.translate_client = translate.Client()
            self.nlp_client = language_v2.LanguageServiceClient()
            self.tts_client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud AI SDKs initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize Google Cloud AI SDKs (ADC missing?): {e}")

    def translate_text(self, text: str, target_language: str = 'hi') -> str:
        """Translate text using Cloud Translation API."""
        if not self.translate_client:
            return f"[Translation Offline] {text}"
            
        def _sync_translate():
            result = self.translate_client.translate(text, target_language=target_language)
            return result.get('translatedText', text)
            
        try:
            return self.executor.submit(_sync_translate).result()
        except Exception as e:
            logger.error(f"Translation API error: {e}")
            return text

    def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment using Cloud Natural Language API."""
        if not self.nlp_client:
            return {"score": 0.0, "magnitude": 0.0}
            
        def _sync_analyze():
            document = language_v2.Document(
                content=text, 
                type_=language_v2.Document.Type.PLAIN_TEXT
            )
            response = self.nlp_client.analyze_sentiment(
                request={'document': document}
            )
            return {
                "score": round(response.document_sentiment.score, 2),
                "magnitude": round(response.document_sentiment.magnitude, 2)
            }
            
        try:
            return self.executor.submit(_sync_analyze).result()
        except Exception as e:
            logger.error(f"NLP API error: {e}")
            return {"score": 0.0, "magnitude": 0.0}

    def synthesize_speech(self, text: str, language_code: str = 'en-IN') -> bytes:
        """Convert text to speech using Cloud Text-to-Speech API."""
        if not self.tts_client:
            return b""
            
        def _sync_tts():
            synthesis_input = texttospeech.SynthesisInput(text=text[:1000]) # Cap to 1000 chars for safety
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name="en-IN-Standard-B" if language_code == 'en-IN' else None
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            return response.audio_content
            
        try:
            return self.executor.submit(_sync_tts).result()
        except Exception as e:
            logger.error(f"TTS API error: {e}")
            return b""
