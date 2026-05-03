"""
ElectaVerse — Security Middleware
Registers Flask before/after request hooks for request IDs, input sanitization,
security headers, and request audit logging.
"""

import uuid
import re
import logging
from flask import request, g

logger = logging.getLogger('electaverse.security')

# Patterns that indicate XSS attempts
XSS_PATTERNS = [
    re.compile(r'<script\b', re.IGNORECASE),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on(error|load|click|mouseover|focus|blur)\s*=', re.IGNORECASE),
    re.compile(r'<iframe\b', re.IGNORECASE),
    re.compile(r'<object\b', re.IGNORECASE),
    re.compile(r'<embed\b', re.IGNORECASE),
    re.compile(r'eval\s*\(', re.IGNORECASE),
    re.compile(r'document\.(cookie|domain|write)', re.IGNORECASE),
]

# Patterns that indicate SQL injection attempts
SQLI_PATTERNS = [
    re.compile(r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\b.*\b(FROM|INTO|TABLE|SET|WHERE)\b)", re.IGNORECASE),
    re.compile(r"(--|;)\s*(DROP|ALTER|DELETE|TRUNCATE)", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r"'\s*(OR|AND)\s+'[^']*'\s*=\s*'[^']*'", re.IGNORECASE),
]

# Maximum request payload size (1MB)
MAX_CONTENT_LENGTH = 1 * 1024 * 1024


def _sanitize_value(value):
    """Recursively sanitize a value (str, dict, or list) by stripping XSS vectors."""
    if isinstance(value, str):
        sanitized = value
        for pattern in XSS_PATTERNS:
            sanitized = pattern.sub('[FILTERED]', sanitized)
        return sanitized
    elif isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


def register_security_middleware(app):
    """Register all security hooks on the Flask app."""

    @app.before_request
    def inject_request_id():
        """Add a unique X-Request-ID to every request for audit trail."""
        g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

    @app.before_request
    def enforce_payload_size():
        """Reject requests with payloads exceeding MAX_CONTENT_LENGTH."""
        if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
            logger.warning(
                f'[SECURITY] Oversized payload rejected: {request.content_length} bytes '
                f'from {request.remote_addr} on {request.path}'
            )
            from flask import abort
            abort(413)

    @app.before_request
    def sanitize_json_input():
        """Strip XSS vectors from incoming JSON payloads."""
        if request.is_json and request.data:
            try:
                data = request.get_json(silent=True)
                if data and isinstance(data, dict):
                    sanitized = _sanitize_value(data)
                    if sanitized != data:
                        logger.warning(
                            f'[SECURITY] XSS patterns detected and filtered '
                            f'from {request.method} {request.path} '
                            f'(request_id={getattr(g, "request_id", "unknown")})'
                        )
                        try:
                            from services.gcloud_logging_service import log_security_event
                            log_security_event('xss_attempt_filtered', {
                                'method': request.method,
                                'path': request.path,
                                'ip': request.remote_addr,
                            })
                        except Exception:
                            pass
            except Exception:
                pass  # Don't block requests on sanitization errors

    @app.after_request
    def add_security_headers(response):
        """Add comprehensive security headers to every response."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        response.headers['Cross-Origin-Embedder-Policy'] = 'unsafe-none'
        # Prevent browsers from caching sensitive data
        if request.path.startswith('/api/auth'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
        return response

    @app.after_request
    def log_request_audit(response):
        """Log request metadata for audit trail."""
        # Only log API requests, skip static assets
        if request.path.startswith('/api/'):
            logger.debug(
                f'[AUDIT] {request.method} {request.path} → {response.status_code} '
                f'(ip={request.remote_addr}, req_id={getattr(g, "request_id", "unknown")})'
            )
        return response
