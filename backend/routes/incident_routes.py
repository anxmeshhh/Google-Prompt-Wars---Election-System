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
    """Trigger AI triage on an incident (Module 3 will add actual AI)."""
    inc = _engine.get_incident(incident_id)
    if not inc:
        return jsonify({'error': 'Incident not found'}), 404

    # Placeholder — Module 3 will wire the Incident Responder agent
    inc.status = 'triaging'
    return jsonify({
        'incident': inc.to_dict(),
        'message': 'AI triage will be available after Module 3 (Agents) is complete.',
    })
