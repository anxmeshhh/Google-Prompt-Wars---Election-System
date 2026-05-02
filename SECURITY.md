# Security Policy

## Supported Versions

| Version | Supported |
|:---|:---|
| 1.0.x (current) | ✅ Active |

## Reporting Vulnerabilities

If you discover a security vulnerability in ElectaVerse, **please do NOT open a public issue**. Instead:

1. **Email**: Send details to [theanimeshgupta@gmail.com](mailto:theanimeshgupta@gmail.com)
2. **Include**: A clear description, steps to reproduce, and potential impact
3. **Response**: You'll receive acknowledgment within 48 hours

## Security Measures

### Authentication & Authorization

- **JWT dual-token system** (access + refresh tokens)
- **Token blacklist** for immediate revocation on logout
- **Brute-force protection**: 5 failed attempts → 15 min lockout
- **PII encryption** using Fernet symmetric encryption
- **Google OAuth 2.0** with `google-auth` token verification
- **SMTP-based OTP** verification for email validation

### Input Security

- **Parameterized SQL queries** throughout — no string concatenation
- **Table name whitelisting** for database explorer
- **XSS sanitization** middleware strips `<script>`, `onerror=`, etc.
- **Email/password validators** enforce format and strength rules

### Transport & Headers

- **Content Security Policy** (CSP) — strict allowlists
- **X-Content-Type-Options**: `nosniff`
- **X-Frame-Options**: `SAMEORIGIN`
- **X-XSS-Protection**: `1; mode=block`
- **Referrer-Policy**: `strict-origin-when-cross-origin`
- **Permissions-Policy**: camera, microphone, geolocation disabled
- **Request IDs** for full audit trail

### Infrastructure

- Deployed on **Google Compute Engine** (us-central1-a)
- **Docker** containerized deployment
- **MySQL 8.0** with connection pooling
- Structured **Google Cloud Logging** for security event auditing

### Dependency Security

- **bandit** static analysis in CI pipeline
- Regular dependency updates via `requirements.txt` pinning
- No `eval()` or `exec()` usage in production code

## Security Testing

```bash
# Run bandit security scanner
cd backend
bandit -r . -x tests/ -ll

# Run security-focused tests
pytest tests/test_security_hardening.py -v
```
