"""
ElectaVerse — Configuration Module
Loads environment variables for database, AI, auth, encryption, and email.
All secrets are loaded from environment — never hardcoded.
"""

import os
import re
from dotenv import load_dotenv

# Load .env — check backend/ dir first, then project root
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    """Application configuration — loaded from environment."""

    # ── Core ──
    SECRET_KEY = os.getenv('SECRET_KEY', 'electaverse-secret-key-dev')
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,https://electaverse.web.app,https://electaverse.firebaseapp.com'
    ).split(',')
    # Allow all Cloudflare tunnel subdomains dynamically using Regex
    CORS_ORIGINS.append(re.compile(r"https://.*\.trycloudflare\.com"))

    # ── AI Services ──
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

    # ── Google OAuth ──
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')

    # ── JWT Authentication ──
    JWT_SECRET = os.getenv('JWT_SECRET', SECRET_KEY)
    JWT_ACCESS_TTL_MINUTES = int(os.getenv('JWT_ACCESS_TTL_MINUTES', '15'))
    JWT_REFRESH_TTL_DAYS = int(os.getenv('JWT_REFRESH_TTL_DAYS', '7'))

    # ── PII Encryption ──
    FERNET_KEY = os.getenv('FERNET_KEY', '')

    # ── Email / OTP ──
    OTP_ENABLED = os.getenv('OTP_ENABLED', 'false').lower() == 'true'
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    SMTP_FROM = os.getenv('SMTP_FROM', '')

    # ── MySQL Database ──
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'electaverse')

    # ── Google Cloud Platform ──
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'electaverse')
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', '')

    # ── Firebase (Spark plan — free) ──
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', '')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', os.getenv('GCP_PROJECT_ID', 'electaverse'))

    # ── Google Cloud Logging ──
    CLOUD_LOGGING_ENABLED = os.getenv('CLOUD_LOGGING_ENABLED', 'false').lower() == 'true'
