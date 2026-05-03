#!/bin/bash
# ElectaVerse — Docker Entrypoint
# Seeds the database on every startup (uses ON DUPLICATE KEY, so idempotent)
# Then starts Gunicorn with eventlet for WebSocket support.

set -e

echo "🗳️  ElectaVerse Backend Starting..."

# Seed constituencies, booths, and simulation config
echo "📦 Running database seed..."
python db/seed.py || echo "⚠️  seed.py failed (DB may not be ready yet, app will retry)"

# Seed election timeline and voter guide content
echo "📦 Running content seed..."
python db/seed_content.py || echo "⚠️  seed_content.py failed (non-critical)"

echo "🚀 Starting Gunicorn..."
exec gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 --timeout 120 app:app
