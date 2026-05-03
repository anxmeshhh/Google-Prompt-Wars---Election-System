"""
ElectaVerse — Chat API Routes
Multi-agent AI chat with real-time simulation context injection.
Every message gets live booth/incident/turnout data so AI answers are grounded in reality.
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
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

    from agents.orchestrator import Orchestrator
    import time as _time
    import eventlet
from eventlet import tpool
    orchestrator = Orchestrator()
    
    def generate_response():
        _start = _time.time()
        full_response = ""
        agent_used = "election_analyst"
        
        try:
            # First, optionally yield live context summary for the UI
            live_summary = {
                'sim_time': live_context.get('clock', {}).get('time_string', 'N/A'),
                'turnout': f"{live_context.get('turnout_percent', 0)}%",
                'open_incidents': live_context.get('open_incidents', 0),
                'avg_queue': live_context.get('avg_queue_length', 0),
            } if live_context else None
            if live_summary:
                yield json.dumps({'type': 'context', 'data': live_summary}) + "\\n"
                
            for chunk_str in orchestrator.route_and_respond_stream(message, live_context, user_role):
                yield chunk_str
                try:
                    chunk = json.loads(chunk_str)
                    if chunk.get('type') == 'metadata':
                        agent_used = chunk.get('agent', agent_used)
                    elif chunk.get('type') == 'chunk':
                        full_response += chunk.get('text', '')
                except Exception:
                    pass
                    
        finally:
            _duration_ms = int((_time.time() - _start) * 1000)
            
            def save_to_db():
                try:
                    Database.execute_write(
                        """INSERT INTO chat_history (user_id, user_message, agent_used, ai_response)
                           VALUES (%s, %s, %s, %s)""",
                        (user['id'], message, agent_used, full_response)
                    )
                except Exception:
                    pass
                
                try:
                    from services.firebase_service import save_agent_metric
                    save_agent_metric(agent_used, _duration_ms, user_role, True)
                except Exception:
                    pass

                try:
                    from services.gcloud_logging_service import log_agent_action
                    log_agent_action(agent_used, 'chat_response', _duration_ms)
                except Exception:
                    pass
                    
            tpool.execute(save_to_db)

    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


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
