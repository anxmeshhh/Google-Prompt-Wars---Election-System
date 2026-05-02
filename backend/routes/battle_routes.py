"""
ElectaVerse — Battle (Prompt Wars) API Routes
Generates AI-vs-AI policy debates and persists them to MySQL, GCS, and Firebase.
"""

from flask import Blueprint, request, jsonify

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

    result = agent.generate_debate(topic, persona_a, persona_b)

    from db.connection import Database
    import json
    import uuid

    # Insert into MySQL database
    battle_id = str(uuid.uuid4())
    try:
        Database.execute_write(
            """INSERT INTO prompt_battles (id, topic, persona_a, persona_b, debate_transcript, winner)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (battle_id, topic, persona_a, persona_b, json.dumps(result.get('debate', [])), result.get('winner', 'Draw'))
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
            'result': result,
        })
    except Exception:
        pass  # GCS is supplementary — don't fail the request

    # Archive in Firebase Firestore
    try:
        from services.firebase_service import save_debate
        save_debate(battle_id, {
            'topic': topic,
            'persona_a': persona_a,
            'persona_b': persona_b,
            'winner': result.get('winner', 'Draw'),
        })
    except Exception:
        pass

    # Log to Google Cloud Logging
    try:
        from services.gcloud_logging_service import log_agent_action
        log_agent_action('DebateModerator', 'debate_generated')
    except Exception:
        pass

    return jsonify({
        'id': battle_id,
        'topic': topic,
        'persona_a': persona_a,
        'persona_b': persona_b,
        'battle_data': result
    })

