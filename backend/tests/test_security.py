"""
ElectaVerse — Security Module Tests
Tests for JWT token management, Fernet encryption, and OTP verification.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.security import (
    create_access_token, create_refresh_token, verify_token,
    encrypt_pii, decrypt_pii
)
from services.email_service import generate_otp, verify_otp


class TestJWT:
    """Tests for JWT token generation and verification."""

    def test_create_access_token(self):
        """Access token should be a non-empty string."""
        token = create_access_token(user_id=1, role='voter')
        assert isinstance(token, str)
        assert len(token) > 20

    def test_verify_access_token(self):
        """Access token should decode to correct payload."""
        token = create_access_token(user_id=42, role='official')
        payload = verify_token(token)
        assert payload is not None
        assert payload['sub'] == 42
        assert payload['role'] == 'official'
        assert payload['type'] == 'access'

    def test_create_refresh_token(self):
        """Refresh token should be a non-empty string."""
        token = create_refresh_token(user_id=1)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_verify_refresh_token(self):
        """Refresh token should decode with type=refresh."""
        token = create_refresh_token(user_id=7)
        payload = verify_token(token)
        assert payload is not None
        assert payload['sub'] == 7
        assert payload['type'] == 'refresh'

    def test_invalid_token_returns_none(self):
        """Garbage token should return None."""
        assert verify_token('not.a.valid.jwt') is None

    def test_empty_token_returns_none(self):
        """Empty token should return None."""
        assert verify_token('') is None


class TestFernetEncryption:
    """Tests for PII encryption/decryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypted data should decrypt back to original."""
        original = "theanimeshgupta@gmail.com"
        encrypted = encrypt_pii(original)
        decrypted = decrypt_pii(encrypted)
        # If FERNET_KEY is set, it should roundtrip. If not, returns original.
        assert decrypted == original

    def test_encrypt_returns_string(self):
        """Encryption should always return a string."""
        result = encrypt_pii("sensitive-data")
        assert isinstance(result, str)


class TestOTP:
    """Tests for OTP generation and verification."""

    def test_generate_otp_format(self):
        """OTP should be a 6-digit string."""
        otp = generate_otp("test@example.com")
        assert len(otp) == 6
        assert otp.isdigit()

    def test_verify_correct_otp(self):
        """Correct OTP should verify successfully."""
        otp = generate_otp("verify@test.com", {"test": "data"})
        valid, data = verify_otp("verify@test.com", otp)
        assert valid is True
        assert data == {"test": "data"}

    def test_verify_wrong_otp(self):
        """Wrong OTP should fail verification."""
        generate_otp("wrong@test.com")
        valid, _ = verify_otp("wrong@test.com", "000000")
        assert valid is False

    def test_verify_expired_otp(self):
        """OTP for unknown email should fail."""
        valid, _ = verify_otp("nobody@test.com", "123456")
        assert valid is False

    def test_otp_consumed_after_use(self):
        """OTP should only work once."""
        otp = generate_otp("once@test.com")
        valid, _ = verify_otp("once@test.com", otp)
        assert valid is True
        # Second attempt should fail
        valid2, _ = verify_otp("once@test.com", otp)
        assert valid2 is False


class TestAuthEndpoints:
    """Tests for new auth endpoints (OTP, refresh)."""

    def test_send_otp_missing_email(self, client):
        """Send OTP without email should return 400."""
        rv = client.post('/api/auth/send-otp', json={})
        assert rv.status_code == 400

    def test_send_otp_invalid_email(self, client):
        """Send OTP with bad email should return 400."""
        rv = client.post('/api/auth/send-otp', json={'email': 'not-an-email'})
        assert rv.status_code == 400

    def test_verify_otp_missing_fields(self, client):
        """Verify OTP without fields should return 400."""
        rv = client.post('/api/auth/verify-otp', json={})
        assert rv.status_code == 400

    def test_refresh_invalid_token(self, client):
        """Refresh with bad token should return 401."""
        rv = client.post('/api/auth/refresh', json={'refresh_token': 'bad'})
        assert rv.status_code == 401
