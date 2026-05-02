"""
ElectaVerse — Analytics API Routes
Serves turnout timelines, incident breakdowns, and queue distributions from DB.
Cached for performance on read-heavy endpoints.
"""

from flask import Blueprint, jsonify
from flask_caching import Cache
from db.connection import Database

analytics_bp = Blueprint('analytics', __name__)

_engine = None
_cache = None


def init_app(engine):
    """Inject simulation engine and cache into this blueprint."""
    global _engine, _cache
    _engine = engine
    # Import cache from app context (lazy to avoid circular imports)
    from app import cache
    _cache = cache


@analytics_bp.route('/api/analytics/turnout', methods=['GET'])
def get_turnout():
    """Get turnout timeline from DB snapshots. Cached 30s."""
    rows = Database.execute(
        """SELECT sim_time, phase, total_votes, turnout_percent, avg_queue_length
           FROM turnout_snapshots ORDER BY tick"""
    )
    return jsonify({'timeline': rows})


@analytics_bp.route('/api/analytics/incidents', methods=['GET'])
def get_incident_analytics():
    """Get incident breakdown by type and severity."""
    by_type = Database.execute(
        "SELECT incident_type, COUNT(*) as count FROM incidents GROUP BY incident_type"
    )
    by_severity = Database.execute(
        "SELECT severity, COUNT(*) as count FROM incidents GROUP BY severity"
    )
    by_status = Database.execute(
        "SELECT status, COUNT(*) as count FROM incidents GROUP BY status"
    )
    return jsonify({
        'by_type': {r['incident_type']: r['count'] for r in by_type},
        'by_severity': {r['severity']: r['count'] for r in by_severity},
        'by_status': {r['status']: r['count'] for r in by_status},
        'total': sum(r['count'] for r in by_type),
    })


@analytics_bp.route('/api/analytics/queues', methods=['GET'])
def get_queue_analytics():
    """Get queue length distribution from live simulation."""
    if not _engine:
        return jsonify({'error': 'Simulation not running'}), 503

    booths = _engine.get_all_booths()
    distribution = {'0-10': 0, '11-30': 0, '31-50': 0, '51-80': 0, '80+': 0}
    for b in booths:
        q = b['queue_length']
        if q <= 10:
            distribution['0-10'] += 1
        elif q <= 30:
            distribution['11-30'] += 1
        elif q <= 50:
            distribution['31-50'] += 1
        elif q <= 80:
            distribution['51-80'] += 1
        else:
            distribution['80+'] += 1

    return jsonify({'distribution': distribution, 'total_booths': len(booths)})


@analytics_bp.route('/api/analytics/agent-metrics', methods=['GET'])
def get_agent_metrics():
    """Return AI agent usage statistics from Firebase Firestore."""
    try:
        from services.firebase_service import get_agent_metrics_summary
        metrics = get_agent_metrics_summary()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'available': False, 'error': str(e), 'agents': {}})

