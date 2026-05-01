"""
ElectaVerse — Flask Application Entry Point
Initializes Flask, SocketIO, database, simulation engine, and all API routes.
"""

import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config
from db.connection import Database
from simulation.engine import SimulationEngine

# ── Create Flask app ──
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# ── CORS ──
CORS(app, origins=Config.CORS_ORIGINS)

# ── SocketIO ──
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ── Initialize Database ──
Database.initialize()

# ── Initialize Simulation Engine ──
engine = SimulationEngine(socketio=socketio)

# ── Register Blueprints ──
from routes.booth_routes import booth_bp, init_app as init_booth_routes
from routes.incident_routes import incident_bp, init_app as init_incident_routes
from routes.auth_routes import auth_bp
from routes.content_routes import content_bp
from routes.chat_routes import chat_bp
from routes.battle_routes import battle_bp
from routes.analytics_routes import analytics_bp, init_app as init_analytics_routes

# Inject engine into routes that need it
init_booth_routes(engine)
init_incident_routes(engine)
init_analytics_routes(engine)

app.register_blueprint(auth_bp)
app.register_blueprint(content_bp)
app.register_blueprint(booth_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(battle_bp)
app.register_blueprint(analytics_bp)


# ── Health Check ──
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'running',
        'simulation': 'active' if engine.running else 'stopped',
        'booths': len(engine.booths),
        'clock': engine.clock.to_dict() if engine.clock else None,
    })


# ── SocketIO Events ──
@socketio.on('connect')
def handle_connect():
    """Send initial state when a client connects."""
    socketio.emit('stats_update', engine.get_stats())
    top_booths = sorted(engine.booths, key=lambda b: b.queue_length, reverse=True)[:20]
    socketio.emit('booth_update', {
        'booths': [b.to_dict() for b in top_booths],
        'clock': engine.clock.to_dict(),
    })


# ── Start simulation when server starts ──
@socketio.on('connect')
def start_simulation_on_first_connect():
    if not engine.running:
        engine.start()


# ── Entry Point ──
if __name__ == '__main__':
    print("\n🗳️  ElectaVerse Backend Starting...")
    print(f"   Booths loaded: {len(engine.booths)}")
    print(f"   Simulation tick: every {engine.tick_interval}s")
    print(f"   API: http://localhost:5000")
    print(f"   WebSocket: ws://localhost:5000\n")

    engine.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
