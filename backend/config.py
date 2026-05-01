"""
ElectaVerse — Configuration Module
Loads environment variables. All tunable parameters live in MySQL (simulation_config table).
"""

import os
from dotenv import load_dotenv

# Load .env — check backend/ dir first, then project root
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    """Application configuration — loaded from environment."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'electaverse-secret-key-dev')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

    # MySQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'theanimesh2005')
    DB_NAME = os.getenv('DB_NAME', 'electaverse')
