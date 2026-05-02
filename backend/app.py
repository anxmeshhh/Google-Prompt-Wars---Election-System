"""
ElectaVerse — Flask Application Entry Point
Initializes Flask, SocketIO, database, simulation engine, and all API routes.
"""

import sys
import os
import logging

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Structured Logging ──
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger('electaverse')

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from config import Config
from db.connection import Database
from simulation.engine import SimulationEngine

# ── Create Flask app ──
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# ── Extensions ──
cache = Cache(config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 60})
cache.init_app(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://"
)

csp = {
    'default-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        '\'unsafe-eval\'',
        '*'
    ]
}
Talisman(app, content_security_policy=csp, force_https=False)

# ── CORS ──
CORS(app, origins=Config.CORS_ORIGINS)

# ── SocketIO ──
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ── Initialize Database ──
Database.initialize()

# ── Initialize Google Cloud Services ──
from services.firebase_service import init_firebase
from services.gcloud_logging_service import init_cloud_logging
init_firebase()
init_cloud_logging()
logger.info('Google Cloud services initialized')

# ── Initialize Simulation Engine ──
engine = SimulationEngine(socketio=socketio)

# ── Register Blueprints ──
from routes.booth_routes import booth_bp, init_app as init_booth_routes
from routes.incident_routes import incident_bp, init_app as init_incident_routes
from routes.auth_routes import auth_bp
from routes.content_routes import content_bp, init_app as init_content_routes
from routes.chat_routes import chat_bp, init_app as init_chat_routes
from routes.battle_routes import battle_bp
from routes.analytics_routes import analytics_bp, init_app as init_analytics_routes
from routes.simulation_routes import sim_bp, init_app as init_sim_routes
from routes.database_routes import db_bp

# Inject engine into routes that need it
init_booth_routes(engine)
init_incident_routes(engine)
init_analytics_routes(engine)
init_chat_routes(engine)
init_content_routes(engine)
init_sim_routes(engine)

app.register_blueprint(auth_bp)
app.register_blueprint(content_bp)
app.register_blueprint(booth_bp)
app.register_blueprint(incident_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(battle_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(sim_bp)
app.register_blueprint(db_bp)


# ── Health Check ──
@app.route('/api/health', methods=['GET'])
@limiter.exempt
@cache.cached(timeout=10)
def health():
    """Return system health status including simulation and booth count."""
    return jsonify({
        'status': 'running',
        'simulation': 'active' if engine.running else 'stopped',
        'booths': len(engine.booths),
        'clock': engine.clock.to_dict() if engine.clock else None,
    })


# ── Global Error Handlers ──
@app.errorhandler(429)
def ratelimit_handler(e):
    """Return JSON on rate limit exceeded instead of HTML."""
    return jsonify({'error': 'Rate limit exceeded. Please slow down.'}), 429


@app.errorhandler(500)
def internal_error(e):
    """Catch unhandled exceptions and return safe JSON."""
    logger.exception('Unhandled server error')
    return jsonify({'error': 'Internal server error'}), 500


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
    logger.info('🗳️  ElectaVerse Backend Starting...')
    logger.info(f'   Booths loaded: {len(engine.booths)}')
    logger.info(f'   Simulation tick: every {engine.tick_interval}s')
    logger.info(f'   API: http://localhost:5000')
    logger.info(f'   WebSocket: ws://localhost:5000')

    engine.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
