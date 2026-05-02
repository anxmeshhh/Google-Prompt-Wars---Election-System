"""
ElectaVerse — Simulation Control API Routes
Provides pause/resume/reset/jump controls for the real-time election simulation engine.
"""

from flask import Blueprint, jsonify, request
from typing import Optional
from simulation.engine import SimulationEngine

sim_bp = Blueprint('sim', __name__)
_engine: Optional[SimulationEngine] = None


def init_app(engine_instance: SimulationEngine) -> None:
    """Register the simulation engine instance for route handlers."""
    global _engine
    _engine = engine_instance


@sim_bp.route('/api/simulation/pause', methods=['POST'])
def pause_sim():
    """Pause the running simulation. Booth queues freeze in place."""
    if not _engine:
        return jsonify({'error': 'Engine offline'}), 500
    _engine.pause()
    return jsonify({'status': 'paused'})


@sim_bp.route('/api/simulation/resume', methods=['POST'])
def resume_sim():
    """Resume a paused simulation. Queues and incidents resume processing."""
    if not _engine:
        return jsonify({'error': 'Engine offline'}), 500
    _engine.resume()
    return jsonify({'status': 'resumed'})


@sim_bp.route('/api/simulation/reset', methods=['POST'])
def reset_sim():
    """Reset the simulation to the beginning of election day (7:00 AM)."""
    if not _engine:
        return jsonify({'error': 'Engine offline'}), 500
    _engine.reset()
    return jsonify({'status': 'reset'})


@sim_bp.route('/api/simulation/jump', methods=['POST'])
def jump_sim():
    """Jump the simulation clock to a specific hour (7-20)."""
    if not _engine:
        return jsonify({'error': 'Engine offline'}), 500
    data = request.json or {}
    hour = int(data.get('hour', 7))
    _engine.jump_time(hour)
    return jsonify({'status': 'jumped', 'hour': hour})

