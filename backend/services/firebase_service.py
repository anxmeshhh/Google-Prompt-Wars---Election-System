"""
ElectaVerse — Firebase Service
Integrates Firebase Admin SDK for Firestore (NoSQL analytics) and Auth verification.
Uses the free Spark plan. Gracefully degrades when credentials are unavailable.
"""

import logging
from datetime import datetime, timezone
from config import Config
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth

logger = logging.getLogger('electaverse.firebase')

# Lazy-loaded Firebase state
_firestore_db = None
_firebase_app = None
_initialized = False


def init_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.
    Returns True if successfully configured, False otherwise.
    """
    global _firestore_db, _firebase_app, _initialized
    if _initialized:
        return _firestore_db is not None

    _initialized = True

    try:
        cred_path = Config.FIREBASE_CREDENTIALS_PATH
        project_id = Config.FIREBASE_PROJECT_ID

        if cred_path:
            # Use explicit service account credentials file
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred, {
                'projectId': project_id,
            })
        elif project_id:
            # Use Application Default Credentials (works on GCE VMs automatically)
            _firebase_app = firebase_admin.initialize_app(options={
                'projectId': project_id,
            })
        else:
            logger.info('Firebase not configured — no credentials or project ID')
            return False

        _firestore_db = firestore.client()
        logger.info(f'Firebase initialized (project={project_id})')
        return True

    except ImportError:
        logger.info('firebase-admin not installed — Firebase features disabled')
        return False
    except Exception as e:
        logger.warning(f'Firebase initialization failed: {e}')
        return False


def is_firebase_available() -> bool:
    """Check if Firebase is configured and operational."""
    if not _initialized:
        init_firebase()
    return _firestore_db is not None


def _get_db():
    """Get Firestore client, or None if unavailable."""
    if not _initialized:
        init_firebase()
    return _firestore_db


# ═══════════════════════════════════════════
# Agent Metrics
# ═══════════════════════════════════════════

def save_agent_metric(agent: str, response_time_ms: int, user_role: str, success: bool = True) -> None:
    """Log an AI agent interaction metric to Firestore."""
    db = _get_db()
    if not db:
        return
    try:
        db.collection('agent_metrics').add({
            'agent': agent,
            'response_time_ms': response_time_ms,
            'user_role': user_role,
            'success': success,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.debug(f'Failed to save agent metric: {e}')


def get_agent_metrics_summary() -> dict:
    """Get aggregated agent usage statistics from Firestore."""
    db = _get_db()
    if not db:
        return {'available': False, 'agents': {}}

    try:
        docs = db.collection('agent_metrics').order_by(
            'timestamp', direction='DESCENDING'
        ).limit(200).stream()

        agent_stats: dict[str, dict] = {}
        for doc in docs:
            data = doc.to_dict()
            agent = data.get('agent', 'unknown')
            if agent not in agent_stats:
                agent_stats[agent] = {
                    'total_calls': 0,
                    'total_time_ms': 0,
                    'successes': 0,
                    'failures': 0,
                }
            agent_stats[agent]['total_calls'] += 1
            agent_stats[agent]['total_time_ms'] += data.get('response_time_ms', 0)
            if data.get('success'):
                agent_stats[agent]['successes'] += 1
            else:
                agent_stats[agent]['failures'] += 1

        # Compute averages
        for agent in agent_stats:
            total = agent_stats[agent]['total_calls']
            if total > 0:
                agent_stats[agent]['avg_response_ms'] = round(
                    agent_stats[agent]['total_time_ms'] / total
                )

        return {'available': True, 'agents': agent_stats}
    except Exception as e:
        logger.debug(f'Failed to get agent metrics: {e}')
        return {'available': False, 'agents': {}}


# ═══════════════════════════════════════════
# Quiz Leaderboard
# ═══════════════════════════════════════════

def save_quiz_score(user_id: int, name: str, score: int, total: int, rank: str) -> None:
    """Save or update a user's Voter IQ quiz score on the leaderboard."""
    db = _get_db()
    if not db:
        return
    try:
        doc_ref = db.collection('quiz_leaderboard').document(str(user_id))
        existing = doc_ref.get()
        # Only update if new score is higher
        if existing.exists and existing.to_dict().get('score', 0) >= score:
            return
        doc_ref.set({
            'user_id': user_id,
            'name': name,
            'score': score,
            'total': total,
            'rank': rank,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.debug(f'Failed to save quiz score: {e}')


def get_quiz_leaderboard(limit: int = 20) -> list[dict]:
    """Get the top quiz scores from Firestore, sorted by score descending."""
    db = _get_db()
    if not db:
        return []
    try:
        docs = db.collection('quiz_leaderboard').order_by(
            'score', direction='DESCENDING'
        ).limit(limit).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.debug(f'Failed to get leaderboard: {e}')
        return []


# ═══════════════════════════════════════════
# Fact-Check Archive
# ═══════════════════════════════════════════

def save_fact_check(user_id: int, claim: str, result: dict) -> str:
    """Archive a fact-check result in Firestore. Returns document ID."""
    db = _get_db()
    if not db:
        return ''
    try:
        doc_ref = db.collection('fact_checks').add({
            'user_id': user_id,
            'claim': claim,
            'verdict': result.get('verdict', 'ERROR'),
            'confidence_score': result.get('confidence_score', 0),
            'reasoning': result.get('reasoning', ''),
            'official_sources': result.get('official_sources', []),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        return doc_ref[1].id
    except Exception as e:
        logger.debug(f'Failed to save fact check: {e}')
        return ''


def get_recent_fact_checks(limit: int = 10) -> list[dict]:
    """Get recent fact-check results from Firestore."""
    db = _get_db()
    if not db:
        return []
    try:
        docs = db.collection('fact_checks').order_by(
            'timestamp', direction='DESCENDING'
        ).limit(limit).stream()
        return [doc.to_dict() for doc in docs]
    except Exception as e:
        logger.debug(f'Failed to get fact checks: {e}')
        return []


# ═══════════════════════════════════════════
# Debate Archive
# ═══════════════════════════════════════════

def save_debate(battle_id: str, debate_data: dict) -> str:
    """Archive a Prompt Wars debate in Firestore."""
    db = _get_db()
    if not db:
        return ''
    try:
        db.collection('debate_archive').document(battle_id).set({
            **debate_data,
            'battle_id': battle_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
        return battle_id
    except Exception as e:
        logger.debug(f'Failed to save debate: {e}')
        return ''


# ═══════════════════════════════════════════
# Analytics Cache
# ═══════════════════════════════════════════

def cache_analytics_snapshot(stats: dict) -> None:
    """Cache an analytics snapshot in Firestore for fast dashboard reads."""
    db = _get_db()
    if not db:
        return
    try:
        db.collection('analytics_cache').document('latest').set({
            **stats,
            'cached_at': datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.debug(f'Failed to cache analytics: {e}')


# ═══════════════════════════════════════════
# Firebase Auth Token Verification
# ═══════════════════════════════════════════

def verify_firebase_token(id_token: str) -> dict | None:
    """
    Verify a Firebase Auth ID token.
    Returns the decoded token payload or None if invalid.
    """
    if not is_firebase_available():
        return None
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return {
            'uid': decoded.get('uid'),
            'email': decoded.get('email'),
            'name': decoded.get('name', ''),
            'provider': decoded.get('firebase', {}).get('sign_in_provider', ''),
        }
    except Exception as e:
        logger.debug(f'Firebase token verification failed: {e}')
        return None
