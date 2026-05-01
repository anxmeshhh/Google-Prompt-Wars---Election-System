"""
ElectaVerse — Battle (Prompt Wars) API Routes
Placeholder — Module 3 (Agents) will wire the Debate Moderator agent.
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

    return jsonify({
        'topic': topic,
        'persona_a': persona_a,
        'persona_b': persona_b,
        'battle_data': result
    })
