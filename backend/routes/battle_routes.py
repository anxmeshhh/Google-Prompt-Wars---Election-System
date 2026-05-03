"""
ElectaVerse — Battle (Prompt Wars) API Routes
Generates AI-vs-AI policy debates and persists them to MySQL, GCS, and Firebase.
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
import eventlet
from eventlet import tpool
import time as _time

battle_bp = Blueprint('battle', __name__)


@battle_bp.route('/api/battle/start', methods=['POST'])
def start_battle():
    """Start a Prompt Wars debate battle."""
    data = request.get_json()
    topic = data.get('topic', '')
    persona_a = data.get('persona_a', 'Policy Hawk')
    persona_b = data.get('persona_b', 'Democracy Dove')

    if not topic:
        return jsonify({'error': 'topic is required'}), 400

    from agents.debate_moderator import DebateModeratorAgent
    agent = DebateModeratorAgent()

    def generate_response():
        _start = _time.time()
        full_response = ""
        
        try:
            for chunk in agent.generate_debate_stream(topic, persona_a, persona_b):
                full_response += chunk
                yield chunk
        finally:
            _duration_ms = int((_time.time() - _start) * 1000)
            
            def save_to_db():
                from db.connection import Database
                import json
                import uuid
                battle_id = str(uuid.uuid4())
                try:
                    Database.execute_write(
                        """INSERT INTO prompt_battles (id, topic, persona_a, persona_b, debate_transcript, winner)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (battle_id, topic, persona_a, persona_b, json.dumps({'markdown': full_response}), 'Draw')
                    )
                except Exception as e:
                    print(f"Failed to save battle to DB: {e}")

                # Persist to Google Cloud Storage
                try:
                    from services.gcs_service import save_debate_transcript
                    save_debate_transcript(battle_id, {
                        'topic': topic,
                        'persona_a': persona_a,
                        'persona_b': persona_b,
                        'result': full_response,
                    })
                except Exception:
                    pass

                # Archive in Firebase Firestore
                try:
                    from services.firebase_service import save_debate
                    save_debate(battle_id, {
                        'topic': topic,
                        'persona_a': persona_a,
                        'persona_b': persona_b,
                        'winner': 'Draw',
                    })
                except Exception:
                    pass

                # Log to Google Cloud Logging
                try:
                    from services.gcloud_logging_service import log_agent_action
                    log_agent_action('DebateModerator', 'debate_generated', _duration_ms)
                except Exception:
                    pass

            tpool.execute(save_to_db)

    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

