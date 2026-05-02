"""
ElectaVerse — Chat API Routes
Multi-agent AI chat with real-time simulation context injection.
Every message gets live booth/incident/turnout data so AI answers are grounded in reality.
"""

from flask import Blueprint, request, jsonify
from db.connection import Database
from routes.auth_routes import _get_user_by_token

chat_bp = Blueprint('chat', __name__)

# Engine reference — set via init_app()
_engine = None

def init_app(engine):
    global _engine
    _engine = engine


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Send a message to the AI assistant with live simulation context."""
    # Auth
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = _get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message is required'}), 400

    user_role = user.get('role', 'voter')

    # Build LIVE context from the running simulation engine
    live_context = {}
    if _engine:
        live_context = _engine.get_stats()

        # Add top congested booths
        top_booths = sorted(_engine.booths, key=lambda b: b.queue_length, reverse=True)[:5]
        live_context['top_congested_booths'] = [b.to_dict() for b in top_booths]

        # Add recent open incidents
        recent = [i for i in _engine.incidents if i.status == 'open']
        recent_sorted = sorted(recent, key=lambda x: x.reported_at, reverse=True)[:5]
        live_context['recent_incidents'] = [i.to_dict() for i in recent_sorted]

    # Route through the orchestrator
    from agents.orchestrator import Orchestrator
    import time as _time
    orchestrator = Orchestrator()
    _start = _time.time()
    result = orchestrator.route_and_respond(message, live_context, user_role)
    _duration_ms = int((_time.time() - _start) * 1000)

    # Persist to chat_history (MySQL)
    try:
        Database.execute_write(
            """INSERT INTO chat_history (user_id, user_message, agent_used, ai_response)
               VALUES (%s, %s, %s, %s)""",
            (user['id'], message, result['agent'], result['response'])
        )
    except Exception:
        pass  # Don't fail the response if DB write fails

    # Track agent metric in Firebase
    try:
        from services.firebase_service import save_agent_metric
        save_agent_metric(result['agent'], _duration_ms, user_role, True)
    except Exception:
        pass

    # Log to Google Cloud Logging
    try:
        from services.gcloud_logging_service import log_agent_action
        log_agent_action(result['agent'], 'chat_response', _duration_ms)
    except Exception:
        pass

    return jsonify({
        'agent': result['agent'],
        'agent_label': result['agent_label'],
        'response': result['response'],
        'user_role': user_role,
        'live_context_summary': {
            'sim_time': live_context.get('clock', {}).get('time_string', 'N/A'),
            'turnout': f"{live_context.get('turnout_percent', 0)}%",
            'open_incidents': live_context.get('open_incidents', 0),
            'avg_queue': live_context.get('avg_queue_length', 0),
        } if live_context else None,
    })


@chat_bp.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """Return chat history for the authenticated user."""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = _get_user_by_token(token)
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401

    rows = Database.execute(
        """SELECT user_message, agent_used, ai_response, created_at
           FROM chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 50""",
        (user['id'],)
    )

    return jsonify({
        'history': [{
            'message': r['user_message'],
            'agent': r['agent_used'],
            'response': r['ai_response'],
            'timestamp': str(r['created_at']),
        } for r in rows],
        'total': len(rows),
    })
