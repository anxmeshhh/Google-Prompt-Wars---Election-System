"""
ElectaVerse — Authentication Routes
Handles user signup, login, logout, and session validation.
"""

import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db.connection import Database

auth_bp = Blueprint('auth', __name__)


def _get_user_by_token(token: str) -> dict | None:
    """Validate session token and return user data."""
    if not token:
        return None
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


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'voter')
    constituency_id = data.get('constituency_id')

    # Validation
    if not name or not email or not password:
        return jsonify({'error': 'Name, email, and password are required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    if role not in ('voter', 'official', 'observer'):
        role = 'voter'

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
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

    # Fetch the new user
    user = Database.execute_one(
        "SELECT id, name, email, role, constituency_id, created_at FROM users WHERE email = %s",
        (email,)
    )

    # Create session token
    token = secrets.token_hex(32)
    expires = datetime.now() + timedelta(days=7)
    Database.execute_write(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
        (token, user['id'], expires)
    )

    # Update last login
    Database.execute_write("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))

    return jsonify({
        'token': token,
        'user': _serialize_user(user),
    }), 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """Login with email and password."""
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
        return jsonify({'error': 'Invalid email or password'}), 401

    # Check password
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Create session token
    token = secrets.token_hex(32)
    expires = datetime.now() + timedelta(days=7)
    Database.execute_write(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (%s, %s, %s)",
        (token, user['id'], expires)
    )

    # Update last login
    Database.execute_write("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))

    return jsonify({
        'token': token,
        'user': _serialize_user(user),
    })


@auth_bp.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user from session token."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = _get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'user': _serialize_user(user)})


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Invalidate session token."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token:
        Database.execute_write("DELETE FROM sessions WHERE token = %s", (token,))
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
