"""
ElectaVerse — Google Cloud Secret Manager Service
Securely retrieves API keys and credentials from Secret Manager in production.
Falls back to environment variables when Secret Manager is unavailable.
"""

import logging
from google.cloud import secretmanager
from config import Config

logger = logging.getLogger('electaverse.secrets')


class GCloudSecretService:
    """Wrapper for Google Cloud Secret Manager — secure credential retrieval."""

    def __init__(self):
        self.client = None
        self.project_id = Config.GCP_PROJECT_ID or 'electaverse'

        try:
            self.client = secretmanager.SecretManagerServiceClient()
            logger.info("Secret Manager initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize Secret Manager: {e}")

    def get_secret(self, secret_id: str, version: str = 'latest') -> str:
        """
        Retrieve a secret value from Secret Manager.
        Falls back to environment variable with same name.
        """
        if not self.client:
            import os
            return os.environ.get(secret_id, '')

        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
            response = self.client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.warning(f"Secret Manager fetch failed for '{secret_id}': {e}")
            import os
            return os.environ.get(secret_id, '')

    def secret_exists(self, secret_id: str) -> bool:
        """Check if a secret exists in Secret Manager."""
        if not self.client:
            return False

        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}"
            self.client.get_secret(request={"name": name})
            return True
        except Exception:
            return False

    def list_secrets(self) -> list[str]:
        """List all available secrets in the project."""
        if not self.client:
            return []

        try:
            parent = f"projects/{self.project_id}"
            secrets = self.client.list_secrets(request={"parent": parent})
            return [s.name.split('/')[-1] for s in secrets]
        except Exception as e:
            logger.warning(f"Failed to list secrets: {e}")
            return []
