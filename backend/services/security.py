"""
ElectaVerse — Security Utilities
JWT token generation/verification and Fernet PII encryption.
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from config import Config

logger = logging.getLogger('electaverse.security')


# ═══════════════════════════════════════════
# JWT Token Management
# ═══════════════════════════════════════════

# In-memory set of revoked JWT tokens (cleared on server restart)
TOKEN_BLACKLIST: set[str] = set()


def blacklist_token(token: str) -> None:
    """Add a token to the revocation blacklist (for logout)."""
    TOKEN_BLACKLIST.add(token)
    logger.info(f'Token blacklisted (total blacklisted: {len(TOKEN_BLACKLIST)})')


def create_access_token(user_id: int, role: str) -> str:
    """Generate a short-lived JWT access token."""
    payload = {
        'sub': str(user_id),
        'role': role,
        'type': 'access',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(
            minutes=Config.JWT_ACCESS_TTL_MINUTES
        ),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def create_refresh_token(user_id: int) -> str:
    """Generate a long-lived JWT refresh token."""
    payload = {
        'sub': str(user_id),
        'type': 'refresh',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(
            days=Config.JWT_REFRESH_TTL_DAYS
        ),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token. Returns payload or None."""
    # Check blacklist first (O(1) lookup)
    if token in TOKEN_BLACKLIST:
        logger.debug('JWT token is blacklisted')
        return None

    try:
        payload = jwt.decode(
            token, Config.JWT_SECRET, algorithms=['HS256'],
            options={'verify_sub': False}
        )
        # Cast sub back to int for DB lookups
        if 'sub' in payload:
            payload['sub'] = int(payload['sub'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug('JWT token expired')
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f'Invalid JWT token: {e}')
        return None


def check_password_strength(password: str) -> dict:
    """
    Check password strength and return feedback.
    Returns: {strong: bool, score: int (0-4), feedback: str}
    """
    import re
    score = 0
    feedback = []

    if len(password) >= 6:
        score += 1
    else:
        feedback.append('Use at least 6 characters')

    if len(password) >= 10:
        score += 1

    if re.search(r'[a-z]', password) and re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append('Mix upper and lowercase letters')

    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append('Add at least one number')

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append('Add a special character for extra strength')

    return {
        'strong': score >= 3,
        'score': min(score, 4),
        'feedback': '; '.join(feedback) if feedback else 'Strong password!'
    }


# ═══════════════════════════════════════════
# Fernet PII Encryption
# ═══════════════════════════════════════════

_fernet = None


def _get_fernet() -> Fernet | None:
    """Lazy-init the Fernet cipher from config."""
    global _fernet
    if _fernet is None and Config.FERNET_KEY:
        try:
            _fernet = Fernet(Config.FERNET_KEY.encode())
        except Exception as e:
            logger.error(f'Failed to init Fernet cipher: {e}')
    return _fernet


def encrypt_pii(plaintext: str) -> str:
    """Encrypt sensitive PII data. Returns ciphertext or original if no key."""
    f = _get_fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt_pii(ciphertext: str) -> str:
    """Decrypt PII data. Returns plaintext or original if decryption fails."""
    f = _get_fernet()
    if f is None:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext
