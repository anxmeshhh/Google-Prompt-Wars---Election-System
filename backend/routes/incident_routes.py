"""
ElectaVerse — Incident API Routes
"""

from flask import Blueprint, request, jsonify

incident_bp = Blueprint('incidents', __name__)

_engine = None


def init_app(engine):
    global _engine
    _engine = engine


@incident_bp.route('/api/incidents', methods=['GET'])
def get_incidents():
    """Get all incidents, filterable by status and severity."""
    status = request.args.get('status')
    severity = request.args.get('severity')
    incidents = _engine.get_incidents(status=status, severity=severity)
    return jsonify({
        'incidents': incidents,
        'total': len(incidents),
    })


@incident_bp.route('/api/incidents', methods=['POST'])
def report_incident():
    """Report a new incident manually."""
    data = request.get_json()
    booth_id = data.get('booth_id')
    description = data.get('description', '')

    if not booth_id or not description:
        return jsonify({'error': 'booth_id and description are required'}), 400

    inc = _engine.report_incident(booth_id, description)
    if not inc:
        return jsonify({'error': 'Booth not found'}), 404

    return jsonify({'incident': inc.to_dict()}), 201


@incident_bp.route('/api/incidents/<incident_id>/triage', methods=['POST'])
def triage_incident(incident_id):
    """Trigger AI triage on an incident."""
    inc = _engine.get_incident(incident_id)
    if not inc:
        return jsonify({'error': 'Incident not found'}), 404

    booth = _engine.get_booth(inc.booth_id)
    
    from agents.incident_responder import IncidentResponderAgent
    agent = IncidentResponderAgent()
    triage_result = agent.triage_incident(inc.to_dict(), booth)
    
    # Update incident with AI recommendations
    inc.status = 'triaging'
    inc.ai_recommendation = triage_result.get('analysis')
    
    # In a real app, we'd save this to DB here. For now, it lives in memory.
    
    return jsonify({
        'incident': inc.to_dict(),
        'triage': triage_result,
        'message': 'AI triage completed successfully.',
    })
