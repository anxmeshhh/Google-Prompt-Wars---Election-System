"""
ElectaVerse — Google Cloud Logging Service
Sends structured log entries to Google Cloud Logging for centralized observability.
Gracefully degrades to standard Python logging when Cloud Logging is unavailable.
"""

import logging
from datetime import datetime, timezone
from config import Config

logger = logging.getLogger('electaverse.cloud_logging')

# Lazy-loaded Cloud Logging client
_cloud_logger = None
_initialized = False


def init_cloud_logging() -> bool:
    """
    Initialize Google Cloud Logging.
    Attaches a Cloud Logging handler to the Python root logger.
    Returns True if successfully configured.
    """
    global _cloud_logger, _initialized
    if _initialized:
        return _cloud_logger is not None

    _initialized = True

    if not Config.CLOUD_LOGGING_ENABLED:
        logger.info('Cloud Logging disabled (CLOUD_LOGGING_ENABLED=false)')
        return False

    try:
        import google.cloud.logging as cloud_logging

        client = cloud_logging.Client(project=Config.GCP_PROJECT_ID or None)
        # Attach Cloud Logging handler to root logger
        client.setup_logging(log_level=logging.INFO)
        _cloud_logger = client.logger('electaverse')
        logger.info(f'Cloud Logging initialized (project={Config.GCP_PROJECT_ID})')
        return True

    except ImportError:
        logger.info('google-cloud-logging not installed — Cloud Logging disabled')
        return False
    except Exception as e:
        logger.warning(f'Cloud Logging initialization failed: {e}')
        return False


def _get_cloud_logger():
    """Get the Cloud Logging logger, or None."""
    if not _initialized:
        init_cloud_logging()
    return _cloud_logger


def log_event(event_type: str, payload: dict, severity: str = 'INFO') -> None:
    """
    Log a structured event to Cloud Logging.
    Falls back to standard Python logging if Cloud Logging is unavailable.

    Args:
        event_type: Event identifier (e.g., 'auth.login', 'agent.response')
        payload: Structured data dict
        severity: Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    entry = {
        'event_type': event_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    cloud = _get_cloud_logger()
    if cloud:
        try:
            cloud.log_struct(entry, severity=severity)
            return
        except Exception as e:
            logger.debug(f'Cloud Logging failed, using local: {e}')

    # Fallback to standard logging
    log_fn = getattr(logger, severity.lower(), logger.info)
    log_fn(f'[{event_type}] {payload}')


def log_auth_event(email: str, action: str, success: bool, ip: str = '') -> None:
    """Log an authentication event (login, register, failed attempt, lockout)."""
    log_event('auth.event', {
        'email': email,
        'action': action,
        'success': success,
        'ip_address': ip,
    }, severity='INFO' if success else 'WARNING')


def log_agent_action(agent: str, action: str, duration_ms: int = 0) -> None:
    """Log an AI agent action (chat response, triage, fact-check, debate)."""
    log_event('agent.action', {
        'agent': agent,
        'action': action,
        'duration_ms': duration_ms,
    })


def log_security_event(event: str, details: dict, severity: str = 'WARNING') -> None:
    """Log a security-related event (brute force, suspicious input, etc.)."""
    log_event('security.event', {
        'security_event': event,
        **details,
    }, severity=severity)


def log_incident_event(incident_id: str, action: str, details: dict = None) -> None:
    """Log an election incident event (created, triaged, resolved)."""
    log_event('incident.event', {
        'incident_id': incident_id,
        'action': action,
        **(details or {}),
    })
