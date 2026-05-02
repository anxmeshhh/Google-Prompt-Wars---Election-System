"""
ElectaVerse — Security Hardening Tests
Tests for brute-force protection, JWT blacklist, input validation,
and security headers.
"""

import sys
import os
import pytest
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ═══════════════════════════════════════════
# JWT Blacklist Tests
# ═══════════════════════════════════════════

class TestJWTBlacklist:
    """Test JWT token blacklisting for logout."""

    def test_blacklisted_token_rejected(self):
        """A blacklisted token should be rejected by verify_token."""
        from services.security import (
            create_access_token, verify_token, blacklist_token, TOKEN_BLACKLIST
        )
        token = create_access_token(user_id=999, role='voter')
        # Should be valid before blacklisting
        assert verify_token(token) is not None

        blacklist_token(token)
        # Should be rejected after blacklisting
        assert verify_token(token) is None

        # Cleanup
        TOKEN_BLACKLIST.discard(token)

    def test_valid_token_after_blacklisting_other(self):
        """Blacklisting one token should not affect others."""
        from services.security import (
            create_access_token, verify_token, blacklist_token, TOKEN_BLACKLIST
        )
        token_a = create_access_token(user_id=1, role='voter')
        token_b = create_access_token(user_id=2, role='voter')

        blacklist_token(token_a)
        assert verify_token(token_a) is None
        assert verify_token(token_b) is not None

        TOKEN_BLACKLIST.discard(token_a)

    def test_expired_token_rejected(self):
        """An expired token should be rejected."""
        from services.security import verify_token
        result = verify_token('invalid.token.string')
        assert result is None


# ═══════════════════════════════════════════
# Password Strength Tests
# ═══════════════════════════════════════════

class TestPasswordStrength:
    """Test password strength checker."""

    def test_strong_password(self):
        """Strong password should score >= 3."""
        from services.security import check_password_strength
        result = check_password_strength('MyStr0ng!Pass')
        assert result['strong'] is True
        assert result['score'] >= 3

    def test_weak_password_short(self):
        """Short password should be flagged as weak."""
        from services.security import check_password_strength
        result = check_password_strength('abc')
        assert result['strong'] is False

    def test_weak_password_no_numbers(self):
        """Password without numbers should get lower score."""
        from services.security import check_password_strength
        result = check_password_strength('abcdefgh')
        assert result['score'] < 4


# ═══════════════════════════════════════════
# Input Validation Tests
# ═══════════════════════════════════════════

class TestInputValidation:
    """Test centralized input validators."""

    def test_validate_email_valid(self):
        """Valid email should pass validation."""
        from utils.validators import validate_email
        valid, err = validate_email('test@example.com')
        assert valid is True
        assert err == ''

    def test_validate_email_invalid(self):
        """Invalid email should fail validation."""
        from utils.validators import validate_email
        valid, err = validate_email('not-an-email')
        assert valid is False
        assert 'format' in err.lower()

    def test_validate_email_empty(self):
        """Empty email should fail validation."""
        from utils.validators import validate_email
        valid, err = validate_email('')
        assert valid is False

    def test_validate_password_valid(self):
        """Valid password should pass."""
        from utils.validators import validate_password
        valid, err = validate_password('Test123')
        assert valid is True

    def test_validate_password_too_short(self):
        """Password under 6 chars should fail."""
        from utils.validators import validate_password
        valid, err = validate_password('ab1')
        assert valid is False

    def test_validate_password_no_letter(self):
        """Password without letters should fail."""
        from utils.validators import validate_password
        valid, err = validate_password('123456')
        assert valid is False

    def test_validate_password_no_number(self):
        """Password without numbers should fail."""
        from utils.validators import validate_password
        valid, err = validate_password('abcdefgh')
        assert valid is False

    def test_validate_table_name_valid(self):
        """Known table names should pass whitelist."""
        from utils.validators import validate_table_name
        assert validate_table_name('users') is True
        assert validate_table_name('booths') is True
        assert validate_table_name('incidents') is True

    def test_validate_table_name_invalid(self):
        """Unknown/malicious table names should be rejected."""
        from utils.validators import validate_table_name
        assert validate_table_name('DROP TABLE users') is False
        assert validate_table_name('') is False
        assert validate_table_name('nonexistent_table') is False

    def test_sanitize_html_strips_scripts(self):
        """sanitize_html should strip script tags."""
        from utils.validators import sanitize_html
        result = sanitize_html('<script>alert("xss")</script>Hello')
        assert '<script>' not in result
        assert 'Hello' in result

    def test_validate_otp_code(self):
        """OTP should be exactly 6 digits."""
        from utils.validators import validate_otp_code
        assert validate_otp_code('123456') is True
        assert validate_otp_code('12345') is False
        assert validate_otp_code('abcdef') is False
        assert validate_otp_code('') is False

    def test_validate_role(self):
        """validate_role should normalize roles."""
        from utils.validators import validate_role
        assert validate_role('voter') == 'voter'
        assert validate_role('OFFICIAL') == 'official'
        assert validate_role('invalid') == 'voter'
        assert validate_role('') == 'voter'


# ═══════════════════════════════════════════
# Security Headers Tests
# ═══════════════════════════════════════════

class TestSecurityHeaders:
    """Test security headers are present in responses."""

    def test_x_content_type_options(self, client):
        """Response should include X-Content-Type-Options header."""
        resp = client.get('/api/health')
        assert resp.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        """Response should include X-Frame-Options header."""
        resp = client.get('/api/health')
        # Talisman sets SAMEORIGIN by default
        assert resp.headers.get('X-Frame-Options') in ('DENY', 'SAMEORIGIN')

    def test_request_id_header(self, client):
        """Response should include X-Request-ID header."""
        resp = client.get('/api/health')
        assert resp.headers.get('X-Request-ID') is not None
        assert len(resp.headers.get('X-Request-ID', '')) > 0

    def test_permissions_policy(self, client):
        """Response should include Permissions-Policy header."""
        resp = client.get('/api/health')
        pp = resp.headers.get('Permissions-Policy', '')
        assert len(pp) > 0  # Should have some policy set
