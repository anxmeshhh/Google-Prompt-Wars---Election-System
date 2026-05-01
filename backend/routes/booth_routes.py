"""
ElectaVerse — Booth API Routes
"""

from flask import Blueprint, request, jsonify

booth_bp = Blueprint('booths', __name__)

# The simulation engine instance will be injected via init_app
_engine = None


def init_app(engine):
    global _engine
    _engine = engine


@booth_bp.route('/api/booths', methods=['GET'])
def get_booths():
    """Get all booth states, optionally filtered by constituency."""
    constituency = request.args.get('constituency')
    booths = _engine.get_all_booths(constituency)
    return jsonify({
        'booths': booths,
        'clock': _engine.clock.to_dict(),
        'total': len(booths),
    })


@booth_bp.route('/api/booths/stats', methods=['GET'])
def get_stats():
    """Get aggregate simulation statistics."""
    return jsonify(_engine.get_stats())


@booth_bp.route('/api/booths/<booth_id>', methods=['GET'])
def get_booth(booth_id):
    """Get a single booth by ID."""
    booth = _engine.get_booth(booth_id)
    if not booth:
        return jsonify({'error': 'Booth not found'}), 404
    return jsonify(booth)


@booth_bp.route('/api/constituencies', methods=['GET'])
def get_constituencies():
    """Get list of all constituencies from DB."""
    from db.connection import Database
    rows = Database.execute("SELECT * FROM constituencies ORDER BY name")
    return jsonify({'constituencies': rows})
