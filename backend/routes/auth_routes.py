"""
ElectaVerse — Authentication Routes
Handles user signup, login, logout, Google OAuth, JWT tokens,
OTP email verification, and session management.
All auth endpoints are rate-limited and protected against brute-force attacks.
"""

import time
import secrets
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import Config
from db.connection import Database
from services.security import (
    create_access_token, create_refresh_token, verify_token,
    encrypt_pii, blacklist_token, check_password_strength
)
from services.email_service import (
    generate_otp, verify_otp, send_otp_email, send_welcome_email
)
from utils.validators import validate_email, validate_password, validate_role

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger('electaverse.auth')

# ── Brute-Force Protection ──
# Maps IP address → list of failed attempt timestamps
_login_attempts: dict[str, list[float]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 15 * 60  # 15 minutes


def _check_brute_force(ip: str) -> bool:
    """Return True if the IP is currently locked out."""
    if ip not in _login_attempts:
        return False
    # Clean old attempts outside lockout window
    cutoff = time.time() - LOCKOUT_DURATION_SECONDS
    _login_attempts[ip] = [t for t in _login_attempts[ip] if t > cutoff]
    return len(_login_attempts[ip]) >= MAX_FAILED_ATTEMPTS


def _record_failed_attempt(ip: str) -> None:
    """Record a failed login attempt for brute-force tracking."""
    if ip not in _login_attempts:
        _login_attempts[ip] = []
    _login_attempts[ip].append(time.time())
    if len(_login_attempts[ip]) >= MAX_FAILED_ATTEMPTS:
        logger.warning(f'[SECURITY] IP {ip} locked out after {MAX_FAILED_ATTEMPTS} failed attempts')
        try:
            from services.gcloud_logging_service import log_security_event
            log_security_event('brute_force_lockout', {'ip': ip})
        except Exception:
            pass


def _clear_failed_attempts(ip: str) -> None:
    """Clear failed attempts after successful login."""
    _login_attempts.pop(ip, None)


def _get_user_by_token(token: str) -> dict | None:
    """Validate session or JWT token and return user data."""
    if not token:
        return None

    # Try JWT first
    payload = verify_token(token)
    if payload and payload.get('type') == 'access':
        user = Database.execute_one(
            "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE id = %s",
            (payload['sub'],)
        )
        return user

    # Fallback to session token (backward compatibility)
    session = Database.execute_one(
        "SELECT user_id, expires_at FROM sessions WHERE token = %s", (token,)
    )
    if not session:
        return None
    if datetime.now() > session['expires_at']:
        Database.execute_write("DELETE FROM sessions WHERE token = %s", (token,))
        return None
    user = Database.execute_one(
        "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE id = %s",
        (session['user_id'],)
    )
    return user


def _create_auth_response(user: dict) -> dict:
    """Generate full auth response with JWT + session tokens."""
    # JWT tokens
    access_token = create_access_token(user['id'], user['role'])
    refresh_token = create_refresh_token(user['id'])

    # Legacy session token (backward compat)
    session_token = secrets.token_hex(32)
    expires = datetime.now() + timedelta(days=Config.JWT_REFRESH_TTL_DAYS)
    Database.execute_write(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
        (session_token, user['id'], expires)
    )

    # Update last login
    Database.execute_write("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))

    return {
        'token': access_token,
        'refresh_token': refresh_token,
        'session_token': session_token,
        'token_type': 'Bearer',
        'expires_in': Config.JWT_ACCESS_TTL_MINUTES * 60,
        'user': _serialize_user(user),
    }


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user with email/password."""
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = validate_role(data.get('role', 'voter'))
    constituency_id = data.get('constituency_id')

    # Validation using centralized validators
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    email_valid, email_err = validate_email(email)
    if not email_valid:
        return jsonify({'error': email_err}), 400

    pw_valid, pw_err = validate_password(password)
    if not pw_valid:
        return jsonify({'error': pw_err}), 400

    # Check if email already exists
    existing = Database.execute_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({'error': 'An account with this email already exists'}), 409

    # Hash password and insert
    pw_hash = generate_password_hash(password)
    try:
        Database.execute_write(
            """INSERT INTO users (name, email, password_hash, role, constituency_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (name, email, pw_hash, role, constituency_id)
        )
    except Exception as e:
        logger.error(f'Registration failed for {email}: {e}')
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

    # Fetch the new user
    user = Database.execute_one(
        "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE email = %s",
        (email,)
    )

    logger.info(f'New user registered: {email} (role={role})')

    # Log to Cloud Logging
    try:
        from services.gcloud_logging_service import log_auth_event
        log_auth_event(email, 'register', True, request.remote_addr)
    except Exception:
        pass

    # Send welcome email (async-safe, non-blocking)
    try:
        send_welcome_email(email, name)
    except Exception:
        pass  # Don't fail registration if email fails

    return jsonify(_create_auth_response(user)), 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate with email and password. Returns JWT + session tokens."""
    client_ip = request.remote_addr

    # Brute-force protection check
    if _check_brute_force(client_ip):
        return jsonify({
            'error': 'Too many failed attempts. Account temporarily locked. Try again in 15 minutes.'
        }), 429

    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    # Find user
    user = Database.execute_one(
        "SELECT id, name, email, password_hash, role, constituency_id, created_at FROM users WHERE email = %s",
        (email,)
    )
    if not user:
        _record_failed_attempt(client_ip)
        try:
            from services.gcloud_logging_service import log_auth_event
            log_auth_event(email, 'login_failed', False, client_ip)
        except Exception:
            pass
        return jsonify({'error': 'Invalid email or password'}), 401

    # Check password
    if not check_password_hash(user['password_hash'], password):
        _record_failed_attempt(client_ip)
        try:
            from services.gcloud_logging_service import log_auth_event
            log_auth_event(email, 'login_failed', False, client_ip)
        except Exception:
            pass
        return jsonify({'error': 'Invalid email or password'}), 401

    # Success — clear failed attempts
    _clear_failed_attempts(client_ip)
    logger.info(f'User login: {email}')

    try:
        from services.gcloud_logging_service import log_auth_event
        log_auth_event(email, 'login_success', True, client_ip)
    except Exception:
        pass

    return jsonify(_create_auth_response(user))


@auth_bp.route('/api/auth/google', methods=['POST'])
def google_login():
    """Login or register with Google OAuth. Returns JWT + session tokens."""
    data = request.get_json()
    token = data.get('token')
    role = data.get('role', 'voter')

    if not token:
        return jsonify({'error': 'Token is required'}), 400

    try:
        # Verify Google token using google-auth library
        client_id = Config.GOOGLE_CLIENT_ID or '855420223700-m7qonpntg4p0i1s3u1fbs52lck69e7t4.apps.googleusercontent.com'
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id
        )
        email = idinfo['email'].lower()
        name = idinfo.get('name', email.split('@')[0])
        google_sub = idinfo.get('sub', '')
        logger.info(f'Google OAuth verified for {email} (sub={google_sub})')
    except ValueError as e:
        logger.warning(f'Invalid Google token attempt: {e}')
        return jsonify({'error': 'Invalid Google token'}), 401

    # Find user
    user = Database.execute_one(
        "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE email = %s",
        (email,)
    )

    if not user:
        # Register new user from Google
        if role not in ('voter', 'official', 'observer'):
            role = 'voter'
        pw_hash = generate_password_hash(secrets.token_hex(16))
        Database.execute_write(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (name, email, pw_hash, role)
        )
        user = Database.execute_one(
            "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE email = %s",
            (email,)
        )
        logger.info(f'New Google user registered: {email}')

        # Send welcome email
        try:
            send_welcome_email(email, name)
        except Exception:
            pass

    return jsonify(_create_auth_response(user))


@auth_bp.route('/api/auth/refresh', methods=['POST'])
def refresh():
    """Refresh an expired access token using a refresh token."""
    data = request.get_json()
    refresh_tok = data.get('refresh_token', '')

    payload = verify_token(refresh_tok)
    if not payload or payload.get('type') != 'refresh':
        return jsonify({'error': 'Invalid or expired refresh token'}), 401

    user = Database.execute_one(
        "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE id = %s",
        (payload['sub'],)
    )
    if not user:
        return jsonify({'error': 'User not found'}), 404

    new_access = create_access_token(user['id'], user['role'])
    return jsonify({
        'token': new_access,
        'token_type': 'Bearer',
        'expires_in': Config.JWT_ACCESS_TTL_MINUTES * 60,
    })


@auth_bp.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    """Send a 6-digit OTP verification code to the given email."""
    data = request.get_json()
    email = data.get('email', '').strip().lower()

    if not email or not _EMAIL_RE.match(email):
        return jsonify({'error': 'Valid email is required'}), 400

    otp = generate_otp(email)
    sent = send_otp_email(email, otp)

    if sent:
        logger.info(f'OTP sent to {email}')
        return jsonify({'message': 'Verification code sent to your email'})
    else:
        # Even if SMTP fails, return success for security (don't leak SMTP status)
        return jsonify({'message': 'Verification code sent to your email'})


@auth_bp.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp_route():
    """Verify a 6-digit OTP code."""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()

    if not email or not code:
        return jsonify({'error': 'Email and code are required'}), 400

    if verify_otp(email, code):
        return jsonify({'verified': True, 'message': 'Email verified successfully'})
    else:
        return jsonify({'error': 'Invalid or expired code'}), 401


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user from JWT or session token."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = _get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'user': _serialize_user(user)})


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Invalidate session and JWT tokens immediately."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        # Blacklist the JWT for immediate revocation
        blacklist_token(token)
        # Also clean up legacy session
        Database.execute_write("DELETE FROM sessions WHERE token = %s", (token,))

    try:
        from services.gcloud_logging_service import log_auth_event
        log_auth_event('', 'logout', True, request.remote_addr)
    except Exception:
        pass

    return jsonify({'message': 'Logged out successfully'})


def _serialize_user(user: dict) -> dict:
    """Serialize user dict for JSON response."""
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
        'constituency_id': user.get('constituency_id'),
        'created_at': str(user['created_at']) if user.get('created_at') else None,
    }
