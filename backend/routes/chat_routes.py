"""
ElectaVerse — Chat API Routes
Placeholder — Module 3 (Agents) will wire the orchestrator and all 5 agents.
"""

from flask import Blueprint, request, jsonify

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """Send a message to the AI assistant."""
    data = request.get_json()
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'message is required'}), 400

    # Placeholder response — Module 3 will add real agent routing
    return jsonify({
        'agent': 'system',
        'response': 'AI agents are being initialized. This will be fully functional after Module 3 is deployed.',
        'message_received': message,
    })
