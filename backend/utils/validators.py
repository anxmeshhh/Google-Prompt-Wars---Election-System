"""
ElectaVerse — Centralized Input Validators
DRY validation functions used across all routes.
Prevents injection, enforces formatting, and ensures data integrity.
"""

import re
from typing import Tuple


# Allowed database table names (whitelist)
ALLOWED_TABLES = {
    'users', 'sessions', 'booths', 'constituencies', 'incidents',
    'turnout_snapshots', 'chat_history', 'prompt_battles',
    'simulation_config', 'peak_multipliers', 'incident_config',
    'fact_check_history', 'voter_iq_scores', 'election_phases',
    'voter_guide_steps',
}

# Valid user roles
VALID_ROLES = {'voter', 'official', 'observer'}

# Email regex (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Dangerous HTML/JS patterns for sanitization
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
SCRIPT_PATTERN = re.compile(r'<script\b[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
EVENT_HANDLER_PATTERN = re.compile(r'\bon\w+\s*=', re.IGNORECASE)


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate an email address format.

    Returns:
        (is_valid, error_message)
    """
    if not email or not isinstance(email, str):
        return False, 'Email is required'

    email = email.strip().lower()

    if len(email) > 254:
        return False, 'Email address is too long'

    if not EMAIL_PATTERN.match(email):
        return False, 'Invalid email format'

    return True, ''


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    Requirements: min 6 chars, at least 1 letter, at least 1 number.

    Returns:
        (is_valid, error_message)
    """
    if not password or not isinstance(password, str):
        return False, 'Password is required'

    if len(password) < 6:
        return False, 'Password must be at least 6 characters long'

    if len(password) > 128:
        return False, 'Password is too long (max 128 characters)'

    if not re.search(r'[a-zA-Z]', password):
        return False, 'Password must contain at least one letter'

    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number'

    return True, ''


def validate_table_name(table: str) -> bool:
    """
    Validate that a table name is in the allowed whitelist.
    Prevents SQL injection via dynamic table names.
    """
    if not table or not isinstance(table, str):
        return False
    return table.strip().lower() in ALLOWED_TABLES


def sanitize_html(text: str) -> str:
    """
    Strip dangerous HTML and JavaScript from text input.
    Used for user-generated content that shouldn't contain markup.
    """
    if not text or not isinstance(text, str):
        return text or ''

    # Remove script tags and content
    text = SCRIPT_PATTERN.sub('', text)
    # Remove event handlers
    text = EVENT_HANDLER_PATTERN.sub('', text)
    # Remove remaining HTML tags
    text = HTML_TAG_PATTERN.sub('', text)

    return text.strip()


def validate_otp_code(code: str) -> bool:
    """
    Validate OTP code format: exactly 6 digits.
    """
    if not code or not isinstance(code, str):
        return False
    return bool(re.match(r'^\d{6}$', code.strip()))


def validate_role(role: str) -> str:
    """
    Validate and normalize a user role.
    Returns the normalized role, or 'voter' as default.
    """
    if not role or not isinstance(role, str):
        return 'voter'
    role = role.strip().lower()
    return role if role in VALID_ROLES else 'voter'
