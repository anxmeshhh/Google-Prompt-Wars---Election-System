"""
ElectaVerse — Email / OTP Service
Sends verification emails and manages OTP codes via SMTP.
"""

import random
import string
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from config import Config

logger = logging.getLogger('electaverse.email')

# In-memory OTP store (production would use Redis/DB)
_otp_store: dict[str, dict] = {}


def generate_otp(email: str, pending_user_data: dict = None) -> str:
    """Generate a 6-digit OTP for the given email and store pending data."""
    otp = ''.join(random.choices(string.digits, k=6))
    _otp_store[email.lower()] = {
        'code': otp,
        'expires': datetime.now() + timedelta(minutes=10),
        'attempts': 0,
        'data': pending_user_data
    }
    return otp


def verify_otp(email: str, code: str) -> tuple[bool, dict | None]:
    """Verify an OTP code. Returns (is_valid, pending_data)."""
    entry = _otp_store.get(email.lower())
    if not entry:
        return False, None
    if datetime.now() > entry['expires']:
        _otp_store.pop(email.lower(), None)
        return False, None
    entry['attempts'] += 1
    if entry['attempts'] > 5:
        _otp_store.pop(email.lower(), None)
        return False, None
    if entry['code'] == code:
        data = entry.get('data')
        _otp_store.pop(email.lower(), None)
        return True, data
    return False, None


def send_otp_email(email: str, otp: str) -> bool:
    """Send an OTP verification email via SMTP."""
    if not Config.SMTP_USER or not Config.SMTP_PASS:
        logger.warning('SMTP not configured — skipping email send')
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🗳️ ElectaVerse — Your Verification Code: {otp}'
        msg['From'] = Config.SMTP_FROM or Config.SMTP_USER
        msg['To'] = email

        html = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto;
                    background: #080c18; color: #f1f5f9; padding: 40px; border-radius: 16px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <span style="font-size: 48px;">🗳️</span>
                <h1 style="font-size: 24px; color: #818cf8; margin-top: 12px;">ElectaVerse</h1>
            </div>
            <p style="font-size: 16px; color: #94a3b8; text-align: center;">
                Your verification code is:
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <span style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #f59e0b;
                             background: rgba(245,158,11,0.1); padding: 16px 32px; border-radius: 12px;
                             border: 1px solid rgba(245,158,11,0.3);">
                    {otp}
                </span>
            </div>
            <p style="font-size: 13px; color: #64748b; text-align: center;">
                This code expires in <strong>10 minutes</strong>. Do not share it.
            </p>
            <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 24px 0;">
            <p style="font-size: 11px; color: #475569; text-align: center;">
                AI-Powered Election Intelligence · Google Prompt Wars 2026
            </p>
        </div>
        """

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.sendmail(Config.SMTP_USER, email, msg.as_string())

        logger.info(f'OTP email sent to {email}')
        return True

    except Exception as e:
        logger.error(f'Failed to send OTP email to {email}: {e}')
        return False


def send_welcome_email(email: str, name: str) -> bool:
    """Send a welcome email after successful registration."""
    if not Config.SMTP_USER or not Config.SMTP_PASS:
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🎉 Welcome to ElectaVerse — Democracy, Decoded.'
        msg['From'] = Config.SMTP_FROM or Config.SMTP_USER
        msg['To'] = email

        html = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto;
                    background: #080c18; color: #f1f5f9; padding: 40px; border-radius: 16px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <span style="font-size: 48px;">🗳️</span>
                <h1 style="font-size: 24px; color: #818cf8; margin-top: 12px;">Welcome, {name}!</h1>
            </div>
            <p style="font-size: 15px; color: #94a3b8; line-height: 1.6;">
                You've joined <strong style="color: #f1f5f9;">ElectaVerse</strong> — an AI-powered
                election intelligence platform built for Google Prompt Wars 2026.
            </p>
            <ul style="color: #94a3b8; font-size: 14px; line-height: 2;">
                <li>📊 Real-time election simulation with 200 booths</li>
                <li>🤖 5 specialized AI agents for election analysis</li>
                <li>⚔️ Prompt Wars debates powered by Gemini</li>
                <li>🔍 AI Fact-Checker with confidence scoring</li>
            </ul>
            <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 24px 0;">
            <p style="font-size: 11px; color: #475569; text-align: center;">
                Powered by Google Gemini · Built for Prompt Wars
            </p>
        </div>
        """

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USER, Config.SMTP_PASS)
            server.sendmail(Config.SMTP_USER, email, msg.as_string())

        logger.info(f'Welcome email sent to {name} ({email})')
        return True

    except Exception as e:
        logger.error(f'Failed to send welcome email: {e}')
        return False
