"""
ElectaVerse — Google Cloud Vision Service
Uses Cloud Vision API for content moderation of user-uploaded election images.
Detects explicit content, violence, and analyzes text within posters/banners.
"""

import logging
from google.cloud import vision
from google.api_core.exceptions import GoogleAPIError
import concurrent.futures

logger = logging.getLogger('electaverse.vision')


class GCloudVisionService:
    """Wrapper for Google Cloud Vision API — content moderation and OCR."""

    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.client = None

        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Cloud Vision API initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize Cloud Vision API: {e}")

    def analyze_image_safety(self, image_bytes: bytes) -> dict:
        """
        Analyze an image for safe search annotations.
        Returns safety scores for adult, violence, racy content.
        """
        if not self.client:
            return {"safe": True, "reason": "Vision API offline"}

        def _sync_detect():
            image = vision.Image(content=image_bytes)
            response = self.client.safe_search_detection(image=image)
            safe = response.safe_search_annotation
            return {
                "adult": vision.Likelihood(safe.adult).name,
                "violence": vision.Likelihood(safe.violence).name,
                "racy": vision.Likelihood(safe.racy).name,
                "safe": safe.adult < 4 and safe.violence < 4 and safe.racy < 4,
            }

        try:
            return self.executor.submit(_sync_detect).result(timeout=10)
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return {"safe": True, "reason": f"Analysis failed: {e}"}

    def detect_text_in_image(self, image_bytes: bytes) -> str:
        """
        Extract text from an image using OCR (e.g., election posters, banners).
        """
        if not self.client:
            return ""

        def _sync_ocr():
            image = vision.Image(content=image_bytes)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            return texts[0].description if texts else ""

        try:
            return self.executor.submit(_sync_ocr).result(timeout=10)
        except Exception as e:
            logger.error(f"Vision OCR error: {e}")
            return ""

    def detect_labels(self, image_bytes: bytes) -> list[dict]:
        """
        Detect labels/objects in an image (e.g., 'ballot box', 'crowd', 'flag').
        """
        if not self.client:
            return []

        def _sync_labels():
            image = vision.Image(content=image_bytes)
            response = self.client.label_detection(image=image, max_results=10)
            return [
                {"label": label.description, "confidence": round(label.score, 2)}
                for label in response.label_annotations
            ]

        try:
            return self.executor.submit(_sync_labels).result(timeout=10)
        except Exception as e:
            logger.error(f"Vision label detection error: {e}")
            return []
